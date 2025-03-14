from slugify import slugify
import arguably
from qec_lego_bench.cli.util import *
from qec_lego_bench.cli.codes import *
from qec_lego_bench.cli.noises import *
from qec_lego_bench.cli.decoders import *
import os
from dataclasses import dataclass, field
from qec_lego_bench.hpc.monte_carlo import LogicalErrorResult
from qec_lego_bench.hpc.monte_carlo import *
from qec_lego_bench.hpc.submitter import *
from qec_lego_bench.hpc.plotter import *
from qec_lego_bench.cli.generate_samples import generate_samples, benchmark_samples
import tempfile
import matplotlib as mpl
from tqdm import tqdm
from .common import (
    DecodingTimeDistribution,
    FloatLogDistribution,
    parametrized_decoder_of,
    MultiDecoderDecodingTimeDistribution,
)


this_dir = os.path.dirname(os.path.abspath(__file__))
time_distribution_template = os.path.join(this_dir, "time_distribution.ipynb")


@arguably.command
def notebook_time_distribution(
    notebook_filepath: str,
    code: CodeCli,
    *,
    noise: NoiseCli = "none",  # type: ignore
    decoder: list[DecoderCli] | None = None,  # type: ignore
    json_filename: str | None = None,
    force_finished: bool = False,
    prepare_only: bool = False,
    no_progress_bar: bool = False,
    max_cpu_hours: float | None = None,
    target_precision: float | None = None,
    slurm_maximum_jobs: int | None = None,
    slurm_cores_per_node: int | None = None,
    slurm_mem_per_job: int | None = None,
    slurm_extra: dict | None = None,
    local_maximum_jobs: int | None = None,
):
    """
    Generate and run a notebook that tunes the decoders for a given code, noise.
    """
    assert os.path.exists(
        time_distribution_template
    ), f"Notebook file not found: {time_distribution_template}"

    if json_filename is None:
        json_filename = os.path.basename(notebook_filepath)
        if json_filename.endswith(".ipynb"):
            json_filename = json_filename[: -len(".ipynb")]
        json_filename += "." + slugify(str(code))
        json_filename += "." + slugify(str(noise))
        json_filename += ".json"

    assert decoder is not None, "please provide a list of decoders"

    parameters = {
        "code": str(code).replace("=", "@"),
        "noise": str(noise).replace("=", "@"),
        "decoders": [
            str(decoder).replace("=", "@").replace(",", ";") for decoder in decoder
        ],
        "json_filename": json_filename,
    }
    if force_finished:
        parameters["force_finished"] = force_finished
    if max_cpu_hours is not None:
        parameters["max_cpu_hours"] = max_cpu_hours
    if target_precision is not None:
        parameters["target_precision"] = target_precision
    if slurm_maximum_jobs is not None:
        parameters["slurm_maximum_jobs"] = slurm_maximum_jobs
    if slurm_cores_per_node is not None:
        parameters["slurm_cores_per_node"] = slurm_cores_per_node
    if slurm_mem_per_job is not None:
        parameters["slurm_mem_per_job"] = slurm_mem_per_job
    if slurm_extra is not None:
        parameters["slurm_extra"] = slurm_extra
    if local_maximum_jobs is not None:
        parameters["local_maximum_jobs"] = local_maximum_jobs

    import papermill

    papermill.execute_notebook(
        time_distribution_template,
        notebook_filepath,
        parameters=parameters,
        prepare_only=prepare_only,
        progress_bar=not no_progress_bar,
        cwd=os.path.dirname(os.path.abspath(notebook_filepath)),
    )


def default_json_filename(code: str, noise: str):
    return "z-time-distribution." + slugify(code) + "." + slugify(noise) + ".json"


@dataclass
class TimeDistributionMonteCarloFunction:
    decoders: list[str]

    def __call__(
        self, shots: int, code: str, noise: str, verbose: bool = False
    ) -> tuple[int, MultiDecoderDecodingTimeDistribution]:

        with tempfile.TemporaryDirectory() as tmp_dir:
            filename = os.path.join(tmp_dir, "tmp")
            generate_samples(
                code=code,
                filename=filename,
                noise=noise,
                shots=shots,
                decoder="none",
                no_print=not verbose,
            )
            results: dict[str, DecodingTimeDistribution] = {}

            for decoder in tqdm(self.decoders, disable=not verbose):
                trace_filename = os.path.join(tmp_dir, f"trace.{slugify(decoder)}.bin")

                result = benchmark_samples(
                    filename=filename,
                    decoder=parametrized_decoder_of(
                        decoder, trace_filename=trace_filename
                    ),
                    no_print=True,
                )
                assert result.shots == shots

                distribution = DecodingTimeDistribution(
                    result=LogicalErrorResult(
                        errors=result.errors, elapsed=result.elapsed
                    ),
                    elapsed=FloatLogDistribution().load_trace(trace_filename),
                )
                results[decoder] = distribution

            return (shots, MultiDecoderDecodingTimeDistribution(results=results))


@dataclass
class TimeDistributionPlotter:
    hdisplay: display.DisplayHandle = field(
        default_factory=lambda: display.display("", display_id=True)
    )
    fig: Figure = field(default_factory=closed_figure)

    def __call__(self, executor: MonteCarloJobExecutor):
        fig = self.fig
        fig.clear()
        assert (
            len(executor.jobs) == 1
        ), "only one job is supported, since each job may have different plots"
        job = list(executor)[0]
        multi: MultiDecoderDecodingTimeDistribution | None = job.result
        if multi is None or len(multi.results) == 0:
            return
        fig.set_size_inches(6, 4 * len(multi.results))
        axes = fig.subplots(
            len(multi.results),
            1,
            squeeze=False,
            gridspec_kw={"hspace": 0.3},
        )
        for i, (decoder, distribution) in enumerate(multi.results.items()):
            ax = axes[i][0]
            ax.clear()
            self.plot(decoder, distribution, ax=ax)
        self.hdisplay.update(fig)

    def plot(
        self, decoder: str, distribution: DecodingTimeDistribution, ax: mpl.axes.Axes
    ):
        x_vec, y_vec = distribution.elapsed.flatten()
        ax.plot(x_vec, y_vec, ".-")
        ax.set_xlabel("decoding time ($s$)")
        ax.set_xscale("log")
        ax.set_ylabel("sample count")
        ax.set_yscale("log")
        ax.title.set_text(
            f"decoder: {decoder}, average={distribution.elapsed.average():.2e}(s)"
        )

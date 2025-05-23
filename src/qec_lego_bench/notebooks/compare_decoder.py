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
from tqdm import tqdm
import matplotlib as mpl
from .common import *


this_dir = os.path.dirname(os.path.abspath(__file__))
compare_decoder_template = os.path.join(this_dir, "compare_decoder.ipynb")
split = "none"


@arguably.command
def notebook_compare_decoder(
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
    srun: bool = False,
    srun_prefix: str = DEFAULT_SRUN_PREFIX,
    srun_suffix: str = DEFAULT_SRUN_SUFFIX,
    srun_wait: bool = False,  # if not wait, output to jobout and joberr
):
    """
    Generate and run a notebook that tunes the decoders for a given code, noise.
    """
    assert os.path.exists(
        compare_decoder_template
    ), f"Notebook file not found: {compare_decoder_template}"

    assert decoder is not None, "please provide a list of decoders"

    code = CodeCli(code)
    noise = NoiseCli(noise)
    decoder = [DecoderCli(d) for d in decoder]

    basename = os.path.basename(notebook_filepath)
    if basename.endswith(".ipynb"):
        basename = basename[: -len(".ipynb")]

    if json_filename is None:
        basename = os.path.basename(notebook_filepath)
        if basename.endswith(".ipynb"):
            basename = basename[: -len(".ipynb")]
        json_filename = default_json_filename(code=code, noise=noise, basename=basename)

    parameters: dict[str, Any] = {
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

    papermill_execute_notebook(
        compare_decoder_template,
        notebook_filepath,
        parameters=parameters,
        prepare_only=prepare_only,
        no_progress_bar=no_progress_bar,
        srun=srun,
        srun_prefix=srun_prefix,
        srun_suffix=srun_suffix,
        srun_wait=srun_wait,
    )


def default_json_filename(
    code: CodeCli | str, noise: NoiseCli | str, basename: str = "z-compare-decoder"
) -> str:
    return f"{basename}.{slugify(str(code))}.{slugify(str(noise))}.json"


@dataclass
class CompareDecoderMonteCarloFunction:
    decoders: list[str]

    def __call__(
        self, shots: int, code: str, noise: str, verbose: bool = False
    ) -> tuple[int, MultiDecoderLogicalErrorRates]:

        with tempfile.TemporaryDirectory() as tmp_dir:
            filename = os.path.join(tmp_dir, "tmp")

            # check if any decoder requires decomposing errors, if so, use that decoder
            representative_decoder: str = "none"
            for decoder in self.decoders:
                if decoder == split:
                    continue
                decoder_instance = DecoderCli(decoder)
                if decoder_instance.decompose_errors:
                    representative_decoder = decoder
                    break

            generate_samples(
                code=code,
                filename=filename,
                noise=noise,
                shots=shots,
                decoder=representative_decoder,
                no_print=not verbose,
            )

            results: dict[str, LogicalErrorResult] = {}
            for decoder in tqdm(self.decoders, disable=not verbose):
                if decoder == split:
                    continue
                result = benchmark_samples(
                    filename=filename,
                    decoder=decoder,
                    no_print=True,
                    remove_initialization_time=True,
                )
                assert result.shots == shots
                results[decoder] = LogicalErrorResult(
                    errors=result.errors, elapsed=result.elapsed
                )

            return shots, MultiDecoderLogicalErrorRates(results=results)


@dataclass
class CompareDecoderPlotter:
    decoders: list[str]

    hdisplay: display.DisplayHandle = field(
        default_factory=lambda: display.display("", display_id=True)
    )
    fig: Figure = field(default_factory=closed_figure)

    def __call__(self, executor: MonteCarloJobExecutor):
        fig = self.fig
        fig.clear()
        axes = fig.subplots(
            len(executor.jobs),
            1,
            squeeze=False,
        )
        for i, job in enumerate(executor):
            ax = axes[i][0]
            ax.clear()
            self.plot(job, ax=ax)
        self.hdisplay.update(fig)

    def plot(self, job: MonteCarloJob, ax: mpl.axes.Axes):
        pL_results = cast(MultiDecoderLogicalErrorRates | None, job.result)
        if pL_results is None:
            return
        best_pL: float | None = None
        best_speed: float | None = None
        best_decoder: str | None = None
        x_vec: list[float] = []
        y_vec: list[float] = []
        previous_decoders: list[str] = []
        for i, decoder in enumerate(self.decoders + ["none"]):
            if decoder == split:
                if len(previous_decoders) > 0:
                    # plot the data
                    ax.plot(
                        x_vec,
                        y_vec,
                        label=decoder_list_label(previous_decoders),
                        marker="o",
                        markersize=5,
                        linestyle="dotted",
                    )
                    x_vec = []
                    y_vec = []
                    previous_decoders = []
                continue
            pL: LogicalErrorResult = pL_results.results[decoder]
            stats = pL.stats_of(job)
            if stats.errors == 0:
                continue
            x_vec.append(stats.speed)
            y_vec.append(1 / stats.failure_rate_value)
            previous_decoders.append(decoder)
            # pL_array[i] = stats.failure_rate_value
            if best_pL is None or stats.failure_rate < best_pL:
                best_pL = stats.failure_rate
                best_speed = stats.speed
                best_decoder = decoder
            elif (
                stats.failure_rate == best_pL
                and best_speed is not None
                and stats.speed > best_speed
            ):
                best_speed = stats.speed
                best_decoder = decoder
        if best_decoder is None:
            return

        ax.set_xlabel("speed ($s^{-1}$)")
        ax.set_xscale("log")
        ax.set_ylabel("accuracy ($p_L^{-1}$)")
        ax.set_yscale("log")
        ax.title.set_text(f"best decoder: {best_decoder}, pL={best_pL:.2uS}")
        ax.legend()


def decoder_list_label(decoders: list[str]):
    assert len(decoders) > 0
    decoder = decoders[-1]
    prefix = os.path.commonprefix(decoders)
    suffix = os.path.commonprefix([x[::-1] for x in decoders])[::-1]
    if len(suffix) + len(prefix) > len(decoder):
        suffix = ""
        variable = decoder[len(prefix) :]
    else:
        variable = decoder[len(prefix) : -len(suffix)]
    return f"{prefix}..{variable}..{suffix}"

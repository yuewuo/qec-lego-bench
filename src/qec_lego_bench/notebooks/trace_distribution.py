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
from .common import *


this_dir = os.path.dirname(os.path.abspath(__file__))
trace_distribution_template = os.path.join(this_dir, "trace_distribution.ipynb")


@arguably.command
def notebook_trace_distribution(
    notebook_filepath: str,
    code: CodeCli,
    *,
    noise: NoiseCli = "none",  # type: ignore
    unit_shots: int | None = None,
    shots: int | None = None,
    decoder: list[DecoderCli] | None = None,  # type: ignore
    gen_json_filename: str | None = None,
    trace_json_filename: str | None = None,
    samples_dir: str | None = None,
    trace_dir: str | None = None,
    prepare_only: bool = False,
    no_progress_bar: bool = False,
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
        trace_distribution_template
    ), f"Notebook file not found: {trace_distribution_template}"

    if gen_json_filename is None:
        basename = os.path.basename(notebook_filepath)
        if basename.endswith(".ipynb"):
            basename = basename[: -len(".ipynb")]
        gen_json_filename = default_gen_json_filename(
            code=code, noise=noise, basename=basename
        )
    if trace_json_filename is None:
        basename = os.path.basename(notebook_filepath)
        if basename.endswith(".ipynb"):
            basename = basename[: -len(".ipynb")]
        trace_json_filename = default_trace_json_filename(
            code=code, noise=noise, basename=basename
        )

    if samples_dir is None:
        samples_dir = os.path.join(os.path.dirname(notebook_filepath), "tmp_samples")
    if trace_dir is None:
        trace_dir = os.path.join(os.path.dirname(notebook_filepath), "tmp_trace")

    assert decoder is not None, "please provide a list of decoders"

    code = CodeCli(code)
    noise = NoiseCli(noise)
    decoder = [DecoderCli(d) for d in decoder]

    parameters: dict[str, Any] = {
        "code": str(code).replace("=", "@"),
        "noise": str(noise).replace("=", "@"),
        "decoders": [
            str(decoder).replace("=", "@").replace(",", ";") for decoder in decoder
        ],
        "gen_json_filename": gen_json_filename,
        "trace_json_filename": trace_json_filename,
        "samples_dir": samples_dir,
        "trace_dir": trace_dir,
    }
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
    if unit_shots is not None:
        parameters["unit_shots"] = unit_shots
    if shots is not None:
        parameters["shots"] = shots

    papermill_execute_notebook(
        trace_distribution_template,
        notebook_filepath,
        parameters=parameters,
        prepare_only=prepare_only,
        no_progress_bar=no_progress_bar,
        srun=srun,
        srun_prefix=srun_prefix,
        srun_suffix=srun_suffix,
        srun_wait=srun_wait,
    )


def default_gen_json_filename(
    code: CodeCli | str,
    noise: NoiseCli | str,
    basename: str = "z-trace-distribution",
) -> str:
    return f"{basename}.gen.{slugify(str(code))}.{slugify(str(noise))}.json"


def default_trace_json_filename(
    code: CodeCli | str,
    noise: NoiseCli | str,
    basename: str = "z-trace-distribution",
) -> str:
    return f"{basename}.trace.{slugify(str(code))}.{slugify(str(noise))}.json"


def samples_filename_of(code: str, noise: str, idx: int, unit_shots: int) -> str:
    return f"{slugify(str(code))}.{slugify(str(noise))}.{unit_shots}.{idx}"


@dataclass
class TraceDistributionSampleGenerationMonteCarloFunction:
    unit_shots: int
    samples_dir: str

    def __call__(
        self, shots: int, code: str, noise: str, decoder: str, idx: int
    ) -> tuple[int, LogicalErrorResult]:
        assert (
            shots == 1
        ), f"only support one batch, generating {self.unit_shots} samples"

        filename = os.path.join(
            self.samples_dir, samples_filename_of(code, noise, idx, self.unit_shots)
        )
        if os.path.exists(filename):
            return (self.unit_shots, LogicalErrorResult())

        start_time = time.time()
        generate_samples(
            code=code,
            filename=filename,
            noise=noise,
            shots=self.unit_shots,
            decoder=decoder,
            seed=idx * 1000 + 123,
            no_print=True,
        )
        elapsed = time.time() - start_time

        return (self.unit_shots, LogicalErrorResult(elapsed=elapsed))


@dataclass
class TraceDistributionMonteCarloFunction:
    unit_shots: int
    samples_dir: str
    trace_dir: str

    def __call__(
        self, shots: int, code: str, noise: str, decoder: str, idx: int
    ) -> tuple[int, LogicalErrorResult]:
        assert shots == 1, f"only support one batch, running {self.unit_shots} trace"

        sample_filename = samples_filename_of(code, noise, idx, self.unit_shots)
        filename = os.path.join(self.samples_dir, sample_filename)
        trace_filename = os.path.join(
            self.trace_dir, f"{slugify(str(decoder))}.{sample_filename}.bin"
        )

        start_time = time.time()
        result = benchmark_samples(
            filename=filename,
            decoder=parametrized_decoder_of(decoder, trace_filename=trace_filename),
            no_print=True,
        )
        assert result.shots == self.unit_shots
        elapsed = time.time() - start_time

        return (self.unit_shots, LogicalErrorResult(elapsed=elapsed))


@dataclass
class TraceTimeDistributionPlotter:
    unit_shots: int
    repeats: int
    trace_dir: str
    code: str
    noise: str
    hdisplay: display.DisplayHandle = field(
        default_factory=lambda: display.display("", display_id=True)
    )
    fig: Figure = field(default_factory=closed_figure)

    def __call__(self, decoders: list[str]):
        fig = self.fig
        fig.clear()
        fig.set_size_inches(6, 4 * len(decoders))
        axes = fig.subplots(
            len(decoders),
            1,
            squeeze=False,
            gridspec_kw={"hspace": 0.3},
        )
        for i, decoder in enumerate(decoders):
            ax = axes[i][0]
            ax.clear()
            self.plot(decoder, ax=ax)
            self.hdisplay.update(fig)

    def plot(
        self,
        decoder: str,
        ax: mpl.axes.Axes,
    ):
        # first read the distribution from the trace files
        distribution = FloatLogDistribution()
        for idx in range(self.repeats):
            sample_filename = samples_filename_of(
                self.code, self.noise, idx, self.unit_shots
            )
            trace_filename = os.path.join(
                self.trace_dir, f"{slugify(str(decoder))}.{sample_filename}.bin"
            )
            distribution += FloatLogDistribution().load_trace(trace_filename)
        x_vec, y_vec = distribution.flatten()
        ax.plot(x_vec, y_vec, ".-")
        ax.set_xlabel("decoding time ($s$)")
        ax.set_xscale("log")
        ax.set_ylabel("sample count")
        ax.set_yscale("log")
        ax.title.set_text(f"{decoder}: L={distribution.average():.2e}(s)")

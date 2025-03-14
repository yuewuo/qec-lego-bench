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
from itertools import product
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib as mpl
from mpl_toolkits.mplot3d import axes3d
from .common import MultiDecoderLogicalErrorRates, parametrized_decoder_of


this_dir = os.path.dirname(os.path.abspath(__file__))
bp_tuner_template = os.path.join(this_dir, "bp_tuner.ipynb")


@arguably.command
def notebook_bp_tuner(
    notebook_filepath: str,
    code: CodeCli,
    *,
    noise: NoiseCli = "none",  # type: ignore
    decoder: DecoderCli = "bposd",  # type: ignore
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
    ms_scaling_factor_choices: list[float] | None = None,
    max_iter_choices: list[int] | None = None,
):
    """
    Generate and run a notebook that tunes the BP decoder for a given code, noise and decoder.
    """
    assert os.path.exists(
        bp_tuner_template
    ), f"Notebook file not found: {bp_tuner_template}"

    assert (
        "ms_scaling_factor" not in decoder.kwargs
    ), "we will iterate over a list of ms_scaling_factor, please provide it via --ms-scaling-factor .."

    assert (
        "max_iter" not in decoder.kwargs
    ), "we will iterate over a list of max_iter, please provide it via --max-iter .."

    parameters: dict[str, Any] = {
        "code": str(code).replace("=", "@"),
        "noise": str(noise).replace("=", "@"),
        "decoder": str(decoder).replace("=", "@"),
    }
    if json_filename is not None:
        parameters["json_filename"] = json_filename
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
    if ms_scaling_factor_choices is not None and len(ms_scaling_factor_choices) > 0:
        parameters["ms_scaling_factor_choices"] = ms_scaling_factor_choices
    if max_iter_choices is not None and len(max_iter_choices) > 0:
        parameters["max_iter_choices"] = max_iter_choices

    import papermill

    papermill.execute_notebook(
        bp_tuner_template,
        notebook_filepath,
        parameters=parameters,
        prepare_only=prepare_only,
        progress_bar=not no_progress_bar,
        cwd=os.path.dirname(os.path.abspath(notebook_filepath)),
    )


def default_json_filename(code: str, noise: str, decoder: str):
    return (
        "z-bp-tuner."
        + slugify(code)
        + "."
        + slugify(noise)
        + "."
        + slugify(decoder)
        + ".json"
    )


@dataclass
class BPTunerMonteCarloFunction:
    max_iter_choices: list[int]
    ms_scaling_factor_choices: list[float]

    def __call__(
        self, shots: int, code: str, noise: str, decoder: str, verbose: bool = False
    ) -> tuple[int, MultiDecoderLogicalErrorRates]:

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

            results: dict[str, LogicalErrorResult] = {}
            for max_iter, ms_scaling_factor in tqdm(
                product(self.max_iter_choices, self.ms_scaling_factor_choices),
                disable=not verbose,
            ):
                parametrized_decoder: str = parametrized_decoder_of(
                    decoder, max_iter=max_iter, ms_scaling_factor=ms_scaling_factor
                )
                # print(f"{parametrized_decoder}: ", end="")
                result = benchmark_samples(
                    filename=filename, decoder=parametrized_decoder, no_print=True
                )
                assert result.shots == shots
                results[parametrized_decoder] = LogicalErrorResult(errors=result.errors)

            return shots, MultiDecoderLogicalErrorRates(results=results)


@dataclass
class BPTunerPlotter:
    max_iter_choices: list[int]
    ms_scaling_factor_choices: list[float]

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
            subplot_kw={"projection": "3d"},
            gridspec_kw={"width_ratios": [2] * len(executor.jobs)},
        )
        for i, job in enumerate(executor):
            ax = axes[i][0]
            ax.clear()
            self.plot(job, ax=ax)
        self.hdisplay.update(fig)

    def plot(self, job: MonteCarloJob, ax: axes3d.Axes3D):
        decoder: str = job.kwargs["decoder"]
        pL_results = cast(MultiDecoderLogicalErrorRates | None, job.result)
        if pL_results is None:
            return
        pL_array: np.ndarray = np.zeros(
            (len(self.max_iter_choices), len(self.ms_scaling_factor_choices)),
            dtype=float,
        )
        best_pL: float | None = None
        best_config: tuple[int, float] | None = None
        for i, max_iter in enumerate(self.max_iter_choices):
            for j, ms_scaling_factor in enumerate(self.ms_scaling_factor_choices):
                parametrized_decoder: str = parametrized_decoder_of(
                    decoder, max_iter=max_iter, ms_scaling_factor=ms_scaling_factor
                )
                pL: LogicalErrorResult = pL_results.results[parametrized_decoder]
                stats = pL.stats_of(job)
                if stats.errors == 0:
                    continue
                pL_array[i][j] = stats.failure_rate_value
                if best_pL is None or stats.failure_rate < best_pL:
                    best_pL = stats.failure_rate
                    best_config = (max_iter, ms_scaling_factor)
        if best_config is None or best_pL is None:
            return

        with np.errstate(divide="ignore"):
            accuracy_array = 1 / pL_array
            accuracy_array[pL_array == 0] = 1 / best_pL  # temporary

        X, Y = np.meshgrid(
            # list(range(len(self.max_iter_choices))),
            [np.log(max_iter) / np.log(10) for max_iter in self.max_iter_choices],
            # self.max_iter_choices,
            self.ms_scaling_factor_choices,
        )
        cmap = cm.coolwarm  # type: ignore
        surface = ax.plot_surface(
            X, Y, accuracy_array.T, cmap=cmap, linewidth=0, antialiased=True
        )
        wireframe = ax.plot_wireframe(
            X, Y, accuracy_array.T, linewidth=0.3, color="black"
        )

        ax.set_zscale("log")  # type: ignore
        ax.set_xticks([0, 1, 2, 3], ["1", "10", "100", "1000"])
        ax.set_xlabel("max_iter")
        ax.set_ylabel("ms_scaling_factor")
        ax.set_zlabel("accuracy $p_L^{-1}$")
        max_iter, ms_scaling_factor = best_config
        ax.title.set_text(
            f"{decoder}: iter={max_iter}, scaling={ms_scaling_factor}, pL={best_pL:.2uS}"
        )

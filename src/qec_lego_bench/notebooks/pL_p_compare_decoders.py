import arguably
from qec_lego_bench.cli.util import *
from qec_lego_bench.cli.codes import *
from qec_lego_bench.cli.noises import *
from qec_lego_bench.cli.decoders import *
import os
from dataclasses import dataclass, field
from qec_lego_bench.hpc.monte_carlo import *
from qec_lego_bench.hpc.submitter import *
from qec_lego_bench.hpc.plotter import *
import matplotlib as mpl
from .common import *
from functools import cached_property
import matplotlib.colors as mcolors
from cycler import cycler
from matplotlib.lines import Line2D


this_dir = os.path.dirname(os.path.abspath(__file__))
pL_p_compare_decoders_template = os.path.join(this_dir, "pL_p_compare_decoders.ipynb")


@arguably.command
def notebook_pL_p_compare_decoders(
    notebook_filepath: str,
    code: list[CodeCli] | None = None,  # type: ignore
    *,
    noise: list[NoiseCli] | None = None,  # type: ignore
    decoder: list[DecoderCli] | None = None,  # type: ignore
    json_filename: str | None = None,
    force_finished: bool = False,
    prepare_only: bool = False,
    no_progress_bar: bool = False,
    max_cpu_hours: float | None = None,
    target_precision: float | None = None,
    high_pL_threshold: float | None = None,
    min_shots: int | None = None,
    max_shots: int | None = None,
    max_errors: int | None = None,
    max_adaptive_min_shots_cpu_hours: float | None = None,
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
    Generate and run a notebook that tunes the decoders for a given sequence of codes and noises.
    """

    assert os.path.exists(
        pL_p_compare_decoders_template
    ), f"Notebook file not found: {pL_p_compare_decoders_template}"

    basename = os.path.basename(notebook_filepath)
    if basename.endswith(".ipynb"):
        basename = basename[: -len(".ipynb")]

    if json_filename is None:
        basename = os.path.basename(notebook_filepath)
        if basename.endswith(".ipynb"):
            basename = basename[: -len(".ipynb")]
        json_filename = default_json_filename(basename=basename)

    assert decoder is not None, "please provide a list of decoders"
    assert code is not None, "please provide a list of codes"
    assert noise is not None, "please provide a list of noises"

    code = [CodeCli(c) for c in code]
    noise = [NoiseCli(n) for n in noise]
    decoder = [DecoderCli(d) for d in decoder]

    sanity_check_parse_codes_and_noises(code, noise)

    parameters: dict[str, Any] = {
        "codes": [str(c).replace("=", "@").replace(",", ";") for c in code],
        "noises": [str(n).replace("=", "@").replace(",", ";") for n in noise],
        "decoders": [str(dec).replace("=", "@").replace(",", ";") for dec in decoder],
        "json_filename": json_filename,
    }
    if force_finished:
        parameters["force_finished"] = force_finished
    if max_cpu_hours is not None:
        parameters["max_cpu_hours"] = max_cpu_hours
    if target_precision is not None:
        parameters["target_precision"] = target_precision
    if high_pL_threshold is not None:
        parameters["high_pL_threshold"] = high_pL_threshold
    if min_shots is not None:
        parameters["min_shots"] = min_shots
    if max_shots is not None:
        parameters["max_shots"] = max_shots
    if max_errors is not None:
        parameters["max_errors"] = max_errors
    if max_adaptive_min_shots_cpu_hours is not None:
        parameters["max_adaptive_min_shots_cpu_hours"] = (
            max_adaptive_min_shots_cpu_hours
        )
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
        pL_p_compare_decoders_template,
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
    basename: str = "z-pL-p-compare-decoders",
) -> str:
    return f"{basename}.json"


def sanity_check_parse_codes_and_noises(
    code: list[CodeCli], noise: list[NoiseCli]
) -> tuple[list[CodeCli], list[NoiseCli]]:
    if len(noise) > 1:
        assert (
            len(code) == len(noise) or len(code) == 1
        ), "please provide either a single code or a list of codes of the same length as the list of noises"
        if len(code) == 1:
            return [code[0]] * len(noise), noise
    if len(code) > 1:
        assert (
            len(noise) == len(code) or len(noise) == 1
        ), "please provide either a single noise or a list of noises of the same length as the list of codes"
        if len(noise) == 1:
            return code, [noise[0]] * len(code)
    return code, noise


@dataclass
class PlPCompareDecodersPlotter:
    """
    This plotter will automatically analyze the code and noise model list and figure out the physical error rate parameter.
    """

    decoders: list[str]
    codes: list[str]
    noises: list[str]
    p_key: str = "p"

    hdisplay: display.DisplayHandle = field(
        default_factory=lambda: display.display("", display_id=True)
    )
    fig: Figure = field(default_factory=closed_figure)

    @cached_property
    def p_in_code(self) -> bool:
        in_code = True
        for code in self.codes:
            if self.p_key in CodeCli(code).kwargs:
                in_code = False
        return in_code

    @cached_property
    def p_in_noise(self) -> bool:
        in_noise = True
        for noise in self.noises:
            if self.p_key in NoiseCli(noise).kwargs:
                in_noise = False
        return in_noise

    def get_p(self, code: str, noise: str) -> float:
        if self.p_in_code:
            return CodeCli(code).kwargs[self.p_key]
        if self.p_in_noise:
            return NoiseCli(noise).kwargs[self.p_key]
        raise ValueError("no p in code or noise")

    def __call__(self, executor: MonteCarloJobExecutor):
        fig = self.fig
        fig.set_size_inches(10, 12)
        ax = fig.gca()
        ax.clear()
        ax.set_xlabel("physical error rate $p$")
        ax.set_ylabel("logical error rate $p_L$")
        ax.set_xlim(1e-5, 1)
        ax.set_xscale("log")
        ax.set_ylim(1e-6, 1)
        ax.set_yscale("log")

        available_jobs = []
        for job in executor:
            if job is None or job.result is None:
                continue
            available_jobs.append(job)

        if len(available_jobs) == 0:
            self.hdisplay.update(fig)
            return

        # group the jobs by the same code and noise with various p
        # (code, noise) -> [(job, p), ...]
        jobs_by_code_and_noise: dict[
            tuple[str, str], list[tuple[MonteCarloJob, float]]
        ] = {}
        for job in available_jobs:
            code_cli = CodeCli(job["code"])
            noise_cli = NoiseCli(job["noise"])
            if self.p_key in code_cli.kwargs:
                p = code_cli.kwargs[self.p_key]
                del code_cli.kwargs[self.p_key]
            else:
                assert (
                    self.p_key in noise_cli.kwargs
                ), f"no kwargs '{self.p_key}' in code or noise"
                p = noise_cli.kwargs[self.p_key]
                del noise_cli.kwargs[self.p_key]
            key = (code_cli.to_str(), noise_cli.to_str())
            if key not in jobs_by_code_and_noise:
                jobs_by_code_and_noise[key] = []
            jobs_by_code_and_noise[key].append((job, p))

        # then check if all the noise are the same; if so, put it to the title instead of legend
        common_noise: None | str = list(jobs_by_code_and_noise.keys())[0][1]
        for code, noise in jobs_by_code_and_noise.keys():
            if noise != common_noise:
                common_noise = None

        title = f"pL-p decoder comparison" + (
            f" ({common_noise} noise)" if common_noise is not None else ""
        )
        ax.set_title(title)

        legend_lines: list[typing.Any] = []
        legend_labels: list[str] = []

        color_cycle = cycler(color=list(mcolors.TABLEAU_COLORS.values()))
        marker_cycle = cycler(marker=["o", "v", "^", "s", "P", "D", "*", "X", "H"])
        for ((code, noise), job_vec), color in zip(
            jobs_by_code_and_noise.items(), color_cycle
        ):
            job_vec.sort(key=lambda x: x[1])  # sort by p
            # check if all the decoders are available, otherwise panic
            for decoder in self.decoders:
                if decoder not in job.result.results:  # type: ignore
                    raise ValueError(
                        f"decoder {decoder} not found in result. "
                        + "You probably add a new decoder for testing. We recommend restarting from scratch "
                        + "because this notebook strictly compares decoders with the exact same sequence of syndrome. "
                        + "Because stim simulation will not produce the same sequence unless given exactly the same machine and version, it's safer to just delete everything and rerun."
                    )
            # plot a line for each decoder
            for decoder, marker in zip(self.decoders, marker_cycle):
                x_vec = []
                y_vec = []
                err_vec = []
                for job, p in job_vec:
                    x_vec.append(p)
                    stats = Stats(
                        stats=sinter.AnonTaskStats(
                            shots=job.shots,
                            errors=job.result.results[decoder].errors,  # type: ignore
                        ),
                    )
                    y_vec.append(stats.failure_rate_value)
                    err_vec.append(stats.failure_rate_uncertainty)
                ax.errorbar(
                    x_vec,
                    y_vec,
                    err_vec,
                    color=color["color"],
                    marker=marker["marker"],
                )

            legend_lines.append(Line2D([0], [0], color=color["color"]))
            label = f"{code}" + (f" ({noise})" if common_noise is None else "")
            legend_labels.append(label)

        # also add decoder legends
        for decoder, marker in zip(self.decoders, marker_cycle):
            legend_lines.append(
                Line2D([0], [0], marker=marker["marker"], color="black")
            )
            legend_labels.append(decoder)

        # TODO: display individual decoder results instead of the joint result.

        ax.legend(legend_lines, legend_labels)
        self.hdisplay.update(fig)

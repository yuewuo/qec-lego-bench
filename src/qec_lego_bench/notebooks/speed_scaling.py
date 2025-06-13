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
from qec_lego_bench.cli.multi_decoding_speed import *
from qec_lego_bench.notebooks.common import *
from cycler import cycler
import matplotlib.colors as mcolors

this_dir = os.path.dirname(os.path.abspath(__file__))
speed_scaling_template = os.path.join(this_dir, "speed_scaling.ipynb")
split = "none"


@arguably.command
def notebook_speed_scaling(
    notebook_filepath: str,
    code: list[CodeCli] | None = None,  # type: ignore
    *,
    noise: list[NoiseCli] | None = None,  # type: ignore
    decoder: list[DecoderCli] | None = None,  # type: ignore
    json_filename: str | None = None,
    force_finished: bool = False,
    prepare_only: bool = False,
    no_progress_bar: bool = False,
    min_shots: int | None = None,
    max_shots: int | None = None,
    min_time: float | None = None,
    local_maximum_jobs: int | None = None,
    repeats: int | None = None,
):
    """
    Generate and run a notebook that tunes the decoders for a given code, noise.
    """
    assert os.path.exists(
        speed_scaling_template
    ), f"Notebook file not found: {speed_scaling_template}"

    assert decoder is not None, "please provide a list of decoders"
    assert code is not None, "please provide a list of codes"
    assert noise is not None, "please provide a list of noises"

    code = [CodeCli(c) for c in code]
    noise = [NoiseCli(n) for n in noise]
    decoder = [DecoderCli(d) for d in decoder]

    basename = os.path.basename(notebook_filepath)
    if basename.endswith(".ipynb"):
        basename = basename[: -len(".ipynb")]

    if json_filename is None:
        basename = os.path.basename(notebook_filepath)
        if basename.endswith(".ipynb"):
            basename = basename[: -len(".ipynb")]
        json_filename = default_json_filename(basename=basename)

    parameters: dict[str, Any] = {
        "codes": [str(c).replace("=", "@").replace(",", ";") for c in code],
        "noises": [str(n).replace("=", "@").replace(",", ";") for n in noise],
        "decoders": [str(dec).replace("=", "@").replace(",", ";") for dec in decoder],
        "json_filename": json_filename,
    }
    if force_finished:
        parameters["force_finished"] = force_finished
    if min_shots is not None:
        parameters["min_shots"] = min_shots
    if max_shots is not None:
        parameters["max_shots"] = max_shots
    if min_time is not None:
        parameters["min_time"] = min_time
    if local_maximum_jobs is not None:
        parameters["local_maximum_jobs"] = local_maximum_jobs
    if repeats is not None:
        parameters["repeats"] = repeats

    papermill_execute_notebook(
        speed_scaling_template,
        notebook_filepath,
        parameters=parameters,
        prepare_only=prepare_only,
        no_progress_bar=no_progress_bar,
    )


def default_json_filename(basename: str = "z-speed-scaling") -> str:
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
class SpeedScalingMonteCarloFunction:
    decoders: list[str]
    min_shots: int
    max_shots: int
    min_time: float

    def __call__(
        self, shots: int, code: str, noise: str, verbose: bool = False, repeat: int = 0
    ) -> tuple[int, MultiDecoderLogicalErrorRates]:

        from qec_lego_bench.cli.multi_decoding_speed import multi_decoding_speed

        # we don't really need shots here
        if verbose:
            print(f"code: {code}, noise: {noise}")
        shots, results = multi_decoding_speed(
            decoders=self.decoders,
            code=code,
            noise=noise,
            no_print=not verbose,
            min_shots=self.min_shots,
            max_shots=self.max_shots,
            min_time=self.min_time,
        )
        return shots, results


@dataclass
class SpeedScalingPlotter:
    codes: list[str]
    noises: list[str]
    decoders: list[str]
    repeats: int = 1
    d_key: str = "d"

    hdisplay: display.DisplayHandle = field(
        default_factory=lambda: display.display("", display_id=True)
    )
    fig: Figure = field(default_factory=closed_figure)

    def __call__(self, executor: MonteCarloJobExecutor):
        fig = self.fig
        fig.set_size_inches(10, 8)
        ax = fig.gca()
        ax.clear()
        ax.set_xlabel("code distances")
        ax.set_ylabel("decoding time ($s$)")
        ax.set_yscale("log")

        available_jobs = []
        for job in executor:
            if job is None or job.result is None:
                continue
            available_jobs.append(job)

        if len(available_jobs) == 0:
            self.hdisplay.update(fig)
            return

        assert len(self.codes) == len(self.noises)

        jobs_by_d: dict[str, list[MonteCarloJob]] = {}
        for job in available_jobs:
            code_cli = CodeCli(job["code"])
            noise_cli = NoiseCli(job["noise"])
            d: str | None = None
            if self.d_key in code_cli.kwargs:
                d = code_cli.kwargs[self.d_key]
            elif self.d_key in noise_cli.kwargs:
                d = noise_cli.kwargs[self.d_key]
            if d is None:
                d = str(job["code"])
            if d not in jobs_by_d:
                jobs_by_d[d] = []
            jobs_by_d[d].append(job)

        d_vec = list(jobs_by_d.keys())
        d_vec.sort()

        color_cycle = cycler(color=list(mcolors.TABLEAU_COLORS.values()))
        marker_cycle = cycler(marker=["o", "v", "^", "s", "P", "D", "*", "X", "H"])

        for decoder, color, marker in zip(self.decoders, color_cycle, marker_cycle):
            dots_x_vec = []
            dots_y_vec = []
            average_y_vec = []
            average_err_vec = []
            for d_idx, d in enumerate(d_vec):
                decoding_time_vec = []
                for job in jobs_by_d[d]:
                    shots = job.shots
                    elapsed: float = job.result.results[decoder].elapsed  # type: ignore
                    dots_x_vec.append(d_idx)
                    decoding_time = elapsed / shots
                    dots_y_vec.append(decoding_time)
                    decoding_time_vec.append(decoding_time)
                average_y_vec.append(sum(decoding_time_vec) / len(decoding_time_vec))
                average_err_vec.append(np.std(decoding_time_vec))
            ax.errorbar(
                range(len(d_vec)),
                average_y_vec,
                average_err_vec,
                label=decoder,
                marker=marker["marker"],
                color=color["color"],
            )
            ax.plot(
                dots_x_vec,
                dots_y_vec,
                linestyle="none",
                marker=marker["marker"],
                color=color["color"],
            )

        ax.set_xticks(range(len(d_vec)), d_vec)
        ax.legend()
        self.hdisplay.update(fig)

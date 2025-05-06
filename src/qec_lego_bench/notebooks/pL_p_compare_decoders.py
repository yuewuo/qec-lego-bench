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
        json_filename = default_json_filename(code=code, noise=noise, basename=basename)

    assert decoder is not None, "please provide a list of decoders"
    assert code is not None, "please provide a list of codes"
    assert noise is not None, "please provide a list of noises"

    sanity_check_parse_codes_and_noises(code, noise)

    parameters: dict[str, Any] = {
        "codes": [str(c).replace("=", "@").replace(",", ";") for c in code],
        "noise": [str(n).replace("=", "@").replace(",", ";") for n in noise],
        "decoders": [str(dec).replace("=", "@").replace(",", ";") for dec in decoder],
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
    code: str, noise: str, basename: str = "z-pL-p-compare-decoders"
) -> str:
    return f"{basename}.{slugify(str(code))}.{slugify(str(noise))}.json"


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
class PlPCompareDecodersMonteCarloFunction:
    decoders: list[str]

    def __call__(
        self, shots: int, code: str, noise: str, verbose: bool = False
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

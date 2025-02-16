import arguably
import sinter
from typing import Optional
from sinter._decoding import sample_decode

from .util import *
from .codes import *
from .noises import *
from .decoders import *
from qec_lego_bench.stats import Stats


@arguably.command
def logical_error_rate(
    code: CodeCli,
    *,
    noise: NoiseCli = "NoNoise",  # type: ignore
    decoder: DecoderCli = "mwpf",  # type: ignore
    max_shots: int = 10_000_000,
    max_errors: int = 10_000,
    num_workers: int = 1,
    no_progress: bool = False,
    no_print: bool = False,
    save_resume_filepath: Optional[str] = None,
    label: Optional[str] = None,
    noise2: NoiseCli = "NoNoise",  # type: ignore
    noise3: NoiseCli = "NoNoise",  # type: ignore
    print_circuit: bool = False,
) -> Stats:
    code_instance = CodeCli(code)()
    noise_instance = NoiseCli(noise)()
    noise2_instance = NoiseCli(noise2)()
    noise3_instance = NoiseCli(noise3)()
    decoder_instance = DecoderCli(decoder)()

    ideal_circuit = code_instance.circuit
    noisy_circuit = noise3_instance(noise2_instance(noise_instance(ideal_circuit)))

    if print_circuit:
        print(noisy_circuit)
        exit(0)

    if hasattr(decoder_instance, "pass_circuit") and decoder_instance.pass_circuit:
        decoder_instance = decoder_instance.with_circuit(noisy_circuit)

    task = sinter.Task(
        circuit=noisy_circuit,
        detector_error_model=noisy_circuit.detector_error_model(
            approximate_disjoint_errors=True
        ),
        decoder=str(decoder),
        collection_options=sinter.CollectionOptions(
            max_shots=max_shots, max_errors=max_errors
        ),
    )
    strong_id = task.strong_id()

    progress_callback = None
    if not no_progress:
        progress_callback = SinterProgressBar(
            name=str(decoder), max_shots=max_shots, max_errors=max_errors
        )
    if (
        no_progress
        and num_workers == 1
        and max_shots == max_errors
        and progress_callback is None
        and save_resume_filepath is None
    ):
        # run single thread instead of sinter.collect, so that the panic information can be collected
        single_result = sample_decode(
            circuit_obj=task.circuit,
            circuit_path=None,
            dem_obj=task.detector_error_model,
            dem_path=None,
            num_shots=max_shots,
            decoder=str(decoder),
            custom_decoders={str(decoder): decoder_instance},
        )
        stats = Stats(single_result)
        if hasattr(decoder_instance, "panic_cases"):
            if len(decoder_instance.panic_cases) > 0:
                for panic_case in decoder_instance.panic_cases:
                    stats.report_panic(panic_case)
        if not no_print:
            print(stats)
        return stats
    else:
        results = sinter.collect(
            num_workers=num_workers,
            tasks=[task],
            progress_callback=progress_callback,
            # print_progress=not no_progress,
            custom_decoders={str(decoder): decoder_instance},
            save_resume_filepath=save_resume_filepath,
        )

        # in case of save_resume_filepath is provided, the results
        # contains a lot of entries. We only need the one that matches strong_id
        for result in results:
            if result.strong_id == strong_id:
                stats = Stats(result)
                if not no_print:
                    print(stats)
                return stats
        raise ValueError("No result found for the given strong_id")


class SinterProgressBar:
    def __init__(self, name: str, max_shots: int, max_errors: int):
        from tqdm.autonotebook import tqdm  # type: ignore

        self.max_shots = max_shots
        self.max_errors = max_errors
        self.pbar_n: Optional[tqdm] = None
        self.pbar_e: Optional[tqdm] = None
        self.name = name

    def __call__(self, progress: sinter.Progress):
        if len(progress.new_stats) == 0:
            # do nothing for the initial callback, no progress bar created
            return
        from tqdm.autonotebook import tqdm  # type: ignore

        stats = Stats(progress.new_stats[0])
        lines = progress.status_message.split("\n")
        shots_index = lines[1].find(" shots_taken ")
        if not shots_index >= 0:
            return
        shots_prefix = lines[2][: shots_index + 12]
        shots = int(shots_prefix[shots_prefix.rfind(" ") + 1 :])
        error_index = lines[1].find(" errors_seen ")
        if not error_index >= 0:
            return
        error_prefix = lines[2][: error_index + 12]
        errors = int(error_prefix[error_prefix.rfind(" ") + 1 :])
        # update pbar
        if self.pbar_n is None:
            self.pbar_n = tqdm(total=self.max_shots, desc="shots")
        if self.pbar_e is None:
            self.pbar_e = tqdm(total=self.max_errors, desc="errors")
        stats = Stats(sinter.AnonTaskStats(shots=shots, errors=errors))
        self.pbar_n.set_description(f"shots ({self.name})")
        self.pbar_n.update(shots - self.pbar_n.n)
        self.pbar_e.set_description(f"errors (pL = {stats.failure_rate:.1uS})")
        self.pbar_e.update(errors - self.pbar_e.n)
        self.pbar_n.refresh()
        self.pbar_e.refresh()

import arguably
import sinter
from .util import *
from .codes import *
from .noises import *
from .decoders import *


@arguably.command
def logical_error_rate(
    code_cli: CodeCli,
    # decoder_cli: DecoderCli,
    *,
    noise_cli: NoiseCli = "NoNoise",
    max_shots: int = 1_000_000,
    max_errors: int = 10_000,
    num_workers: int = 1,
):
    code = code_cli()
    noise = noise_cli()
    # decoder = decoder_cli()

    ideal_circuit = code.circuit
    noisy_circuit = noise(ideal_circuit)
    # print(noisy_circuit)
    dem = noisy_circuit.detector_error_model()

    task = sinter.Task(
        circuit=noisy_circuit,
        collection_options=sinter.CollectionOptions(
            max_shots=max_shots, max_errors=max_errors
        ),
    )
    sinter.collect(
        num_workers=num_workers,
        tasks=[task],
        decoders=["mw_parity_factor"],
        # decoders=["pymatching"],
        print_progress=True,
    )

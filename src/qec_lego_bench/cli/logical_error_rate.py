import arguably
import sinter

from .util import *
from .codes import *
from .noises import *
from .decoders import *
from ldpc.sinter_decoders import SinterBpOsdDecoder, SinterBeliefFindDecoder


@arguably.command
def logical_error_rate(
    code_cli: CodeCli,
    *,
    noise_cli: NoiseCli = "NoNoise",  # type: ignore
    decoder_cli: DecoderCli = "mwpf",  # type: ignore
    max_shots: int = 10_000_000,
    max_errors: int = 10_000,
    num_workers: int = 1,
):
    code = code_cli()
    noise = noise_cli()
    decoder = decoder_cli()

    ideal_circuit = code.circuit
    noisy_circuit = noise(ideal_circuit)

    task = sinter.Task(
        circuit=noisy_circuit,
        collection_options=sinter.CollectionOptions(
            max_shots=max_shots, max_errors=max_errors
        ),
    )
    sinter.collect(
        num_workers=num_workers,
        tasks=[task],
        decoders=[str(decoder_cli)],
        # decoders=["mw_parity_factor"],
        # decoders=["bposd"],
        # decoders=["bposd1"],
        # decoders=["pymatching"],
        print_progress=True,
        custom_decoders={str(decoder_cli): decoder},
    )

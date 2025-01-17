import arguably
from .util import *
from .codes import *
from .noise import *


@arguably.command
def logical_error_rate(
    code_cli: CodeCli,
    noise_cli: NoiseCli,
):
    code = code_cli()
    ideal_circuit = code.circuit
    noise = noise_cli()
    noisy_circuit = noise(ideal_circuit)
    # print(noisy_circuit)
    dem = noisy_circuit.detector_error_model()
    print(dem)

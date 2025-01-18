from .noise import Noise
from dataclasses import dataclass
from qec_lego_bench.cli.noises import noise_cli
import stim


@noise_cli("NoNoise")
@dataclass
class NoNoise(Noise):
    """
    no noise
    """

    def __call__(self, circuit: stim.Circuit) -> stim.Circuit:
        return circuit.copy()

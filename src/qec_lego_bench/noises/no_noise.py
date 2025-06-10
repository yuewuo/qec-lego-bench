from .noise import Noise
from dataclasses import dataclass
from qec_lego_bench.cli.noises import noise_cli
import stim


@noise_cli("NoNoise", "none")
@dataclass
class NoNoise(Noise):
    """
    no noise
    """

    p: float = 0.3  # no effect, but allows certain tools to read the noise strength

    def __call__(self, circuit: stim.Circuit) -> stim.Circuit:
        return circuit.copy()

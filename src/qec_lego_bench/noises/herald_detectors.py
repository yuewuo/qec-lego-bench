from .noise import Noise
from dataclasses import dataclass
from qec_lego_bench.cli.noises import noise_cli
import stim
from mwpf.heralded_dem import add_herald_detectors, remove_herald_detectors


@noise_cli("add_all_herald_detectors")
@dataclass
class AddAllHeraldDetectors(Noise):
    def __call__(self, circuit: stim.Circuit) -> stim.Circuit:
        return add_herald_detectors(circuit)


@noise_cli("remove_all_herald_detectors")
@dataclass
class RemoveAllHeraldDetectors(Noise):
    def __call__(self, circuit: stim.Circuit) -> stim.Circuit:
        return remove_herald_detectors(circuit)

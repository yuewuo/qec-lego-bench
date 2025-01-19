from dataclasses import dataclass
from qec_lego_bench.codes.code import Code
from qec_lego_bench.cli.codes import code_cli
import stim
from typing import Optional


@code_cli("NoisyUnrotatedSurfaceCode", "noisy_usc", "usc")
@dataclass
class NoisyUnrotatedSurfaceCode(Code):
    d: int
    p: float = 0.0
    # if not specified, rounds = distance
    rounds: Optional[int] = None
    basis: str = "X"

    def __post_init__(self):
        assert self.p >= 0
        assert self.p <= 1
        rounds = self.d if self.rounds is None else self.rounds
        assert self.basis.lower() in ["x", "y"]
        code_task = "surface_code:unrotated_memory_" + self.basis.lower()
        self._circuit = stim.Circuit.generated(
            code_task,
            rounds=rounds,
            distance=self.d,
            after_clifford_depolarization=self.p,
            before_round_data_depolarization=self.p,
            before_measure_flip_probability=self.p,
            after_reset_flip_probability=self.p,
        )

    @property
    def circuit(self) -> stim.Circuit:
        return self._circuit

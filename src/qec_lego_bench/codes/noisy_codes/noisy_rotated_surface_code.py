from dataclasses import dataclass
from qec_lego_bench.codes.code import Code
from qec_lego_bench.cli.codes import code_cli
import stim
from typing import Optional


@code_cli("NoisyRotatedSurfaceCode", "noisy_rsc", "rsc")
@dataclass
class NoisyRotatedSurfaceCode(Code):
    d: int
    p: float = 0.0
    # if not specified, rounds = distance
    rounds: Optional[int] = None
    basis: str = "X"
    after_clifford_depolarization_ratio: float = 1.0
    before_round_data_depolarization_ratio: float = 1.0
    before_measure_flip_probability_ratio: float = 1.0
    after_reset_flip_probability_ratio: float = 1.0

    def __post_init__(self):
        assert self.p >= 0
        assert self.p <= 1
        rounds = self.d if self.rounds is None else self.rounds
        assert self.basis.lower() in ["x", "y"]
        code_task = "surface_code:rotated_memory_" + self.basis.lower()
        self._circuit = stim.Circuit.generated(
            code_task,
            rounds=rounds,
            distance=self.d,
            after_clifford_depolarization=self.p
            * self.after_clifford_depolarization_ratio,
            before_round_data_depolarization=self.p
            * self.before_round_data_depolarization_ratio,
            before_measure_flip_probability=self.p
            * self.before_measure_flip_probability_ratio,
            after_reset_flip_probability=self.p
            * self.after_reset_flip_probability_ratio,
        )

    @property
    def circuit(self) -> stim.Circuit:
        return self._circuit

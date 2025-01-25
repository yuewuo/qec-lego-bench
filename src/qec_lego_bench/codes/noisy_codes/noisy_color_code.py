from dataclasses import dataclass
from qec_lego_bench.codes.code import Code
from qec_lego_bench.cli.codes import code_cli
import stim
from typing import Optional


@code_cli("NoisyColorCode", "noisy_color", "color")
@dataclass
class NoisyColorCode(Code):
    d: int
    p: float = 0.0
    # if not specified, rounds = distance
    rounds: Optional[int] = None

    after_clifford_depolarization: Optional[float] = None
    before_round_data_depolarization: Optional[float] = None
    before_measure_flip_probability: Optional[float] = None
    after_reset_flip_probability: Optional[float] = None

    def __post_init__(self):
        assert self.p >= 0
        assert self.p <= 1
        rounds = self.d if self.rounds is None else self.rounds
        self._circuit = stim.Circuit.generated(
            "color_code:memory_xyz",
            rounds=rounds,
            distance=self.d,
            after_clifford_depolarization=self.after_clifford_depolarization or self.p,
            before_round_data_depolarization=self.before_round_data_depolarization
            or self.p,
            before_measure_flip_probability=self.before_measure_flip_probability
            or self.p,
            after_reset_flip_probability=self.after_reset_flip_probability or self.p,
        )

    @property
    def circuit(self) -> stim.Circuit:
        return self._circuit

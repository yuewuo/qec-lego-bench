from .noise import Noise
from dataclasses import dataclass
from qec_lego_bench.cli.noise import noise_cli
import stim


@noise_cli("FlipNoise")
@dataclass
class FlipNoise(Noise):
    """
    add a flip noise to all the qubits in the circuit with probability p,
    when a TICK instruction is encountered.
    """

    p: float
    basis: str = "X"  # "X", "Z" or "Y"

    def __post_init__(self):
        assert self.basis in ["X", "Y", "Z"]
        assert self.p >= 0
        assert self.p <= 1

    def _add_noise(self, circuit: stim.Circuit):
        all_qubits = list(range(circuit.num_qubits))
        if self.p == 1:
            circuit.append(self.basis, all_qubits)
        elif self.p > 0:
            circuit.append(self.basis + "_ERROR", all_qubits, self.p)

    def __call__(self, circuit: stim.Circuit) -> stim.Circuit:
        noisy_c = stim.Circuit()
        for op in circuit:
            noisy_c.append(op)
            if op.name == "TICK":
                self._add_noise(noisy_c)
        return noisy_c

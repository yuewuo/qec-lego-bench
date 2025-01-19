from .noise import Noise
from dataclasses import dataclass
from qec_lego_bench.cli.noises import noise_cli
import stim


@noise_cli("FlipNoise", "flip")
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
        circuit.append(self.basis + "_ERROR", all_qubits, self.p)

    def __call__(self, circuit: stim.Circuit) -> stim.Circuit:
        noisy = stim.Circuit()
        self.add_noise_to(circuit, noisy)
        return noisy

    def add_noise_to(self, circuit: stim.Circuit, noisy: stim.Circuit):
        for op in circuit:  # type: ignore
            if op.name == "TICK":
                noisy.append(op)
                self._add_noise(noisy)
            elif op.name == "REPEAT":
                repeat = stim.Circuit()
                self.add_noise_to(op.body_copy(), repeat)
                noisy.append(
                    stim.CircuitRepeatBlock(
                        body=repeat,
                        repeat_count=op.repeat_count,
                    )
                )
            else:
                noisy.append(op)

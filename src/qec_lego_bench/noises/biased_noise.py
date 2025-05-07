from .noise import Noise
from dataclasses import dataclass
from qec_lego_bench.cli.noises import noise_cli
import stim


@noise_cli("BiasedNoise", "biased")
@dataclass
class BiasedNoise(Noise):
    """
    add a biased noise to all the qubits in the circuit with probability p,
    when a TICK instruction is encountered.

    The bias is calculated as eta = pX / (pY + pZ) when the bias axes is X.
    We also have p = pX + pY + pZ

    - pX = eta * p / (1 + eta)
    - pY = pZ = p / (1 + eta) / 2
    """

    p: float
    basis: str = "X"  # "X", "Z" or "Y"
    eta: float = 0.5  # by default depolarizing noise

    def __post_init__(self):
        assert self.p >= 0
        assert self.p <= 1
        assert self.eta >= 0

    def _add_noise(self, circuit: stim.Circuit):
        all_qubits = list(range(circuit.num_qubits))
        for basis in ["X", "Y", "Z"]:
            if self.p_of_basis(basis) > 0:
                circuit.append(basis + "_ERROR", all_qubits, self.p_of_basis(basis))

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

    @property
    def p_bias(self) -> float:
        if self.eta == float("inf"):
            return self.p
        return self.eta / (1 + self.eta) * self.p

    @property
    def p_unbiased(self) -> float:
        if self.eta == float("inf"):
            return 0
        return self.p / (1 + self.eta) / 2

    def p_of_basis(self, basis: str) -> float:
        if self.basis == basis:
            return self.p_bias
        else:
            return self.p_unbiased

from .noise import Noise
from dataclasses import dataclass, replace
from qec_lego_bench.cli.noises import noise_cli
import stim
from mwpf.ref_circuit import RefCircuit, RefInstruction


@noise_cli("ErasureConversion", "erasure_conversion", "EC")
@dataclass
class ErasureConversion(Noise):
    """
    convert existing pauli errors partly into heralded errors

    DEPOLARIZE1 -> HERALDED_ERASE
    DEPOLARIZE2 -> HERALDED_ERASE * 2 independently on each qubit (due to limitation of stim==1.15.0)
    TODO: # CORRELATED_ERROR -> HERALDED_PAULI_CHANNEL_1 independently
    TODO: # ELSE_CORRELATED_ERROR -> HERALDED_PAULI_CHANNEL_1 independently
    TODO: # E -> same as CORRELATED_ERROR
    TODO: # PAULI_CHANNEL_1 -> HERALDED_PAULI_CHANNEL_1
    TODO: PAULI_CHANNEL_2 -> HERALDED_PAULI_CHANNEL_1 * 2 independently
    X_ERROR -> HERALDED_PAULI_CHANNEL_1
    Y_ERROR -> HERALDED_PAULI_CHANNEL_1
    Z_ERROR -> HERALDED_PAULI_CHANNEL_1

    """

    rate: float
    no_detectors: bool = False

    def __post_init__(self):
        assert self.rate >= 0
        assert self.rate <= 1

    def __call__(self, circuit: stim.Circuit) -> stim.Circuit:
        if self.rate == 0:
            return circuit.copy()
        ref_circuit = RefCircuit.of(circuit)
        instructions: list[RefInstruction] = []
        for instruction in ref_circuit:
            if instruction.name == "DEPOLARIZE1" or instruction.name == "DEPOLARIZE2":
                p: float = instruction.gate_args[0]
                instructions.append(
                    replace(instruction, gate_args=(p * (1 - self.rate),))
                )
                new_ins = RefInstruction.new_heralded_erase(
                    instruction.targets, min(1, 4 / 3 * p * self.rate)
                )
                instructions.append(new_ins)
                if not self.no_detectors:
                    for rec in new_ins.recs:
                        instructions.append(RefInstruction.new_detector((rec,)))
            elif (
                instruction.name == "X_ERROR"
                or instruction.name == "Y_ERROR"
                or instruction.name == "Z_ERROR"
            ):
                basis = instruction.name[0]
                p = instruction.gate_args[0]
                instructions.append(
                    replace(instruction, gate_args=(p * (1 - self.rate),))
                )
                new_ins = RefInstruction.new_heralded_pauli_channel_1(
                    instruction.targets,
                    pI=p * self.rate,
                    **{"p" + basis: p * self.rate}
                )
                instructions.append(new_ins)
                if not self.no_detectors:
                    for rec in new_ins.recs:
                        instructions.append(RefInstruction.new_detector((rec,)))
            else:
                instructions.append(instruction)
        new_circuit = RefCircuit.of(instructions)
        return new_circuit.circuit()

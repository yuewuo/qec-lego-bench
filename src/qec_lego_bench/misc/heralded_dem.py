"""
Regular Detector Error Model (DEM) does not contain the information of the heralded error.
This HeraldedDetectorErrorModel class provides additional information on the heralded errors.
It is capable of reading bits from the detector which corresponds to the heralded error indicator.

Note that in order to let the tool read a heralded error in the circuit, it is required that 
the heralded error is detected using `DETECTOR rec[...]` where `rec[...]` corresponds to the heralded event.
To avoid user from doing this manually, we have a function that automatically adds such detections:
``
"""

import stim
from .ref_circuit import RefCircuit


class HeraldedDetectorErrorModel:
    def __init__(self, circuit: stim.Circuit):
        self.circuit = RefCircuit(circuit)
        # iterate over all heralded errors in the circuit and construct the
        # mapping from (RefInstruction, bias) to the heralded detector
        heralded_errors: dict[tuple[int, int], int] = {}
        for instruction in enumerate(self.circuit):
            if instruction.name == "HERALDED_ERASE":
                for target in enumerate(instruction.targets):
                    assert isinstance(target, stim.GateTarget)
            elif instruction.name == "HERALDED_PAULI_CHANNEL_1":
                # TODO: implement
                ...
            elif "HERALDED" in instruction.name:
                raise NotImplementedError(
                    f"Instruction {instruction.name} has 'HERALDED' in its name but is not implemented yet."
                )


def add_heralded_detectors(circuit: stim.Circuit) -> stim.Circuit:
    """
    Add detectors for heralded errors to the circuit, if they do not present in the original circuit.
    Note that the circuit will be fully expanded after this function. The added heralded detectors
    will be at the end of the circuit.
    """
    ref_circuit = RefCircuit(circuit)
    # TODO:
    return ref_circuit.to_circuit()

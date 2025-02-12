"""
The Circuit object in stim always write in relative measurement index, 
which is great for writing loops but not so great for analyzing the measurements.
Especially, if we want to analyze the effect of certain heralded errors, we will
need to keep the rest of the measurements in the same place. However, removing or 
adding one heralded error will change all the relative measurement indices, making it
especially hard to track and analyze the circuit.

This class is used to convert the relative measurement index to referenced measurement
 and vice versa. This will allow us to manipulate the circuit by adding or removing
heralded errors more easily.

This is done by adding a custom class `ReferenceRec` in place of the normal `GateTarget`
object returned by the `stim.target_rec(lookback)` function.
In constrast to the negative integer `lookback` parameters, the `bias` integer is a non-negative
index bias over the `RefInstruction` that generates the measurements.
In this way, we are free to manipulate the instructions without worrying that the measurements
indices are messed up.
The `RefCircuit` object will automatically calculate the new relative indices so that the circuit
works properly, and also it will generate a mapping between indices of the old circuit and new circuit.

```python

```
"""

import stim
from dataclasses import dataclass
from typing import List, Iterator, Iterable


@dataclass(frozen=True)
class ReferenceRec:
    instruction: "RefInstruction"
    bias: int

    def __post_init__(self):
        if self.bias < 0:
            raise ValueError("The bias must be a non-negative integer.")


@dataclass(frozen=True)
class RefInstruction:
    name: str
    targets: tuple[stim.GateTarget | ReferenceRec, ...]
    gate_args: tuple[float, ...]
    tag: str
    num_measurements: int


@dataclass
class RefIterInfo:
    measurement_indices: dict[int, int]
    # before the current instruction is added to the measurement
    num_measurement: int
    instruction: RefInstruction
    stim_instruction: stim.CircuitInstruction
    relative_targets: list[stim.GateTarget]
    rel_to_abs: dict[int, tuple[int, int]]


class RefCircuit:
    def __init__(self, circuit: stim.Circuit):
        self.instructions: list[RefInstruction] = []
        rec: list[ReferenceRec] = []
        for instruction in circuit.flattened():
            # rewrite the gate target to absolute measurement indices
            abs_targets: list[stim.GateTarget | ReferenceRec] = []
            for target in instruction.targets_copy():
                if target.is_measurement_record_target:
                    abs_targets.append(rec[target.value])
                else:
                    abs_targets.append(target)
            # construct the instruction
            ref_instruction = RefInstruction(
                name=instruction.name,
                targets=tuple(abs_targets),
                gate_args=tuple(instruction.gate_args_copy()),
                tag=instruction.tag,
                num_measurements=instruction.num_measurements,
            )
            self.instructions.append(ref_instruction)
            # add the measurement to the measurement list
            for index in range(instruction.num_measurements):
                rec.append(
                    ReferenceRec(
                        instruction=ref_instruction,
                        bias=index,
                    )
                )

    def __repr__(self) -> str:
        repr_str = "RefCircuit: {  # not executable\n"
        repr_str += "\n".join("    " + e for e in str(self).splitlines())
        repr_str += "\n}"
        return repr_str

    def __str__(self) -> str:
        # print the circuit in absolute indices; this helps writing test cases
        code_str = ""
        for iter_info in self.iterate_over_instruction():
            instruction_str = str(iter_info.stim_instruction)
            # change all the relative indices to absolute indices
            for relative_index, (abs_index, count) in iter_info.rel_to_abs.items():
                # this count checking is safe because "rec[..]" becomes "rec[..\C"
                # in the tag parameter, and the character "]" cannot appear elsewhere
                assert instruction_str.count(f"rec[{relative_index}]") == count
                instruction_str = instruction_str.replace(
                    f"rec[{relative_index}]", f"abs[{abs_index}]"
                )
            if len(code_str) > 0:
                code_str += "\n"
            code_str += instruction_str
        return code_str

    def __iter__(self) -> Iterator[RefInstruction]:
        for instruction in self.instructions:
            yield instruction

    def to_circuit(self) -> stim.Circuit:
        circuit = stim.Circuit()
        for iter_info in self.iterate_over_instruction():
            circuit.append(iter_info.stim_instruction)
        return circuit

    def iterate_over_instruction(self) -> Iterable[RefIterInfo]:
        measurement_indices: dict[int, int] = {}
        num_measurement = 0
        for instruction in self.instructions:
            # convert the reference instruction into relative index
            relative_targets = []
            rel_to_abs: dict[int, tuple[int, int]] = {}  # relative -> (absolute, count)
            for ref_target in instruction.targets:
                if isinstance(ref_target, ReferenceRec):
                    assert id(ref_target.instruction) in measurement_indices, (
                        f"referring to a measurement that does not exist, "
                        + f"id={id(ref_target.instruction)} instruction={ref_target.instruction}"
                    )
                    index = (
                        measurement_indices[id(ref_target.instruction)]
                        + ref_target.bias
                    )
                    relative_index = index - num_measurement
                    relative_targets.append(stim.target_rec(relative_index))
                    if relative_index in rel_to_abs:
                        abs_index, count = rel_to_abs[relative_index]
                        assert abs_index == index
                        rel_to_abs[relative_index] = (abs_index, count + 1)
                    else:
                        rel_to_abs[relative_index] = (index, 1)
                else:
                    relative_targets.append(ref_target)
            # construct stim instruction using relative index
            stim_instruction = stim.CircuitInstruction(
                name=instruction.name,
                targets=relative_targets,
                gate_args=instruction.gate_args,
                tag=instruction.tag,
            )
            yield RefIterInfo(
                measurement_indices=measurement_indices,
                num_measurement=num_measurement,
                instruction=instruction,
                stim_instruction=stim_instruction,
                relative_targets=relative_targets,
                rel_to_abs=rel_to_abs,
            )
            # calculate the starting measurement index of the ref-instruction
            assert (
                id(instruction) not in measurement_indices
            ), f"Duplicate instruction found, id={id(instruction)}, instruction={instruction}"
            measurement_indices[id(instruction)] = num_measurement
            num_measurement += instruction.num_measurements

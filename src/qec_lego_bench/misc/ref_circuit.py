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

This is done by adding a custom class `RefRec` in place of the normal `GateTarget`
object returned by the `stim.target_rec(lookback)` function.
In contrast to the negative integer `lookback` parameters, the `bias` integer is a non-negative
index bias over the `RefInstruction` that generates the measurements.
In this way, we are free to manipulate the instructions without worrying that the measurements
indices are messed up.
The `RefCircuit` object will automatically calculate the new relative indices so that the circuit
works properly, and also it will generate a mapping between indices of the old circuit and new circuit.

```python
circuit = stim.Circuit(...)
ref_circuit = RefCircuit(circuit)
print(ref_circuit)  # print the circuit in absolute indices
circuit_2 = ref_circuit.to_circuit()  # convert the ref_circuit back to stim.Circuit
print(circuit_2)  # print the circuit in relative indices
```
"""

import stim
from dataclasses import dataclass, field
from typing import Iterator, Iterable


@dataclass(frozen=True)
class RefRec:
    instruction: "RefInstruction"
    bias: int

    def __post_init__(self):
        if self.bias < 0:
            raise ValueError("The bias must be a non-negative integer.")


@dataclass(frozen=True)
class RefInstruction:
    name: str
    targets: tuple[stim.GateTarget | RefRec, ...]
    gate_args: tuple[float, ...]
    tag: str
    rec: list[RefRec] = field(default_factory=list)

    @property
    def num_measurements(self) -> int:
        return len(self.rec)


@dataclass
class RefIterInfo:
    measurement_indices: dict[int, int]
    # before the current instruction is added to the measurement
    num_measurements: int
    instruction: RefInstruction
    stim_instruction: stim.CircuitInstruction
    relative_targets: list[stim.GateTarget]
    rel_to_abs: dict[int, tuple[int, int]]


class RefCircuit:
    def __init__(self, circuit: stim.Circuit | Iterable[RefInstruction] | None = None):
        if circuit is None:
            self.instructions: list[RefInstruction] = []
            return
        if not isinstance(circuit, stim.Circuit):
            self.instructions = list(circuit)
            self.sanity_check()
            return
        self.instructions = []
        rec: list[RefRec] = []
        for instruction in circuit.flattened():
            # rewrite the gate target to absolute measurement indices
            abs_targets: list[stim.GateTarget | RefRec] = []
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
            )
            self.instructions.append(ref_instruction)
            # add the measurement to the measurement list
            for bias in range(instruction.num_measurements):
                reference_rec = RefRec(
                    instruction=ref_instruction,
                    bias=bias,
                )
                ref_instruction.rec.append(reference_rec)
                rec.append(reference_rec)
        self.sanity_check()

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

    def rec(self) -> list[RefRec]:
        rec: list[RefRec] = []
        for instruction in self.instructions:
            rec.extend(instruction.rec)
        return rec

    def to_circuit(self) -> stim.Circuit:
        circuit = stim.Circuit()
        for iter_info in self.iterate_over_instruction():
            circuit.append(iter_info.stim_instruction)
        return circuit

    def iterate_over_instruction(self) -> Iterable[RefIterInfo]:
        measurement_indices: dict[int, int] = {}
        num_measurements = 0
        for instruction in self.instructions:
            # convert the reference instruction into relative index
            relative_targets = []
            rel_to_abs: dict[int, tuple[int, int]] = {}  # relative -> (absolute, count)
            for ref_target in instruction.targets:
                if isinstance(ref_target, RefRec):
                    assert id(ref_target.instruction) in measurement_indices, (
                        f"referring to a measurement that does not exist, "
                        + f"id={id(ref_target.instruction)} instruction={ref_target.instruction}"
                    )
                    index = (
                        measurement_indices[id(ref_target.instruction)]
                        + ref_target.bias
                    )
                    relative_index = index - num_measurements
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
                num_measurements=num_measurements,
                instruction=instruction,
                stim_instruction=stim_instruction,
                relative_targets=relative_targets,
                rel_to_abs=rel_to_abs,
            )
            # calculate the starting measurement index of the ref-instruction
            assert (
                id(instruction) not in measurement_indices
            ), f"Duplicate instruction found, id={id(instruction)}, instruction={instruction}"
            measurement_indices[id(instruction)] = num_measurements
            num_measurements += instruction.num_measurements

    def __getitem__(self, key: slice) -> "RefInstruction | RefCircuit":
        if isinstance(key, int):
            return self.instructions[key]
        elif isinstance(key, slice):
            return RefCircuit(self.instructions[key])
        else:
            raise TypeError("Invalid key type")

    def __add__(self, other: "RefCircuit | RefInstruction") -> "RefCircuit":
        if isinstance(other, RefInstruction):
            return RefCircuit(self.instructions + [other])
        elif isinstance(other, RefCircuit):
            return RefCircuit(self.instructions + other.instructions)
        else:
            raise NotImplemented()

    def __radd__(self, other: "RefCircuit | RefInstruction") -> "RefCircuit":
        if isinstance(other, RefInstruction):
            return RefCircuit([other] + self.instructions)
        elif isinstance(other, RefCircuit):
            return RefCircuit(other.instructions + self.instructions)
        else:
            raise NotImplemented()

    def sanity_check(self) -> None:
        # check if there are any duplicate instruction: id -> index
        existing_instruction: dict[int, int] = {}
        for index, instruction in enumerate(self.instructions):
            assert id(instruction) not in existing_instruction, (
                f"Duplicate instruction found, id={id(instruction)}, "
                + f"instruction={instruction}, "
                + f"previous index={existing_instruction[id(instruction)]}, "
                + f"current index={index}; if you want to repeat the same "
                + "circuit, considering using sub_circuit + sub_circuit.clone()"
            )
            existing_instruction[id(instruction)] = index
        # check if all the references are valid in the current context
        rec = self.rec()
        rec_index_of: dict[int, int] = {id(rec): index for index, rec in enumerate(rec)}
        assert len(rec_index_of) == len(rec), "has duplicate RefRec object"
        # check if the instructions only reference to the available RefRec objects
        # also check that all the RefRec objects refer to a valid Instruction
        previous_rec_set: set[int] = set()
        previous_instruction_set: set[int] = set()
        for instruction in self.instructions:
            for ref_target in instruction.targets:
                if isinstance(ref_target, RefRec):
                    assert id(ref_target) in previous_rec_set, (
                        f"Reference to a RefRec object that does not appear previously, "
                        + f"id={id(ref_target)}, ref_target={ref_target}"
                    )
                    assert id(ref_target.instruction) in previous_instruction_set
            for ref_rec in instruction.rec:
                assert id(ref_rec.instruction) == id(instruction)  # must refer itself
                previous_rec_set.add(id(ref_rec))
            previous_instruction_set.add(id(instruction))
        # check that the number of measurements is correct
        for iter_info in self.iterate_over_instruction():
            assert (
                iter_info.stim_instruction.num_measurements
                == iter_info.instruction.num_measurements
            )

    def clone(self) -> "RefCircuit":
        """
        make a deep copy of the RefCircuit object, creating branch new instructions
        with different ids, but keeping the circuit the same
        """
        new_instructions: list[RefInstruction] = []
        old_rec = self.rec()
        old_rec_index_of: dict[int, int] = {
            id(rec): index for index, rec in enumerate(old_rec)
        }
        new_rec: list[RefRec] = []
        for instruction in self.instructions:
            new_instruction = RefInstruction(
                name=instruction.name,
                targets=tuple(
                    (
                        new_rec[old_rec_index_of[id(target)]]
                        if isinstance(target, RefRec)
                        else target
                    )
                    for target in instruction.targets
                ),
                gate_args=instruction.gate_args,
                tag=instruction.tag,
            )
            for bias in range(instruction.num_measurements):
                reference_rec = RefRec(
                    instruction=new_instruction,
                    bias=bias,
                )
                new_instruction.rec.append(reference_rec)
                new_rec.append(reference_rec)
            new_instructions.append(new_instruction)
        return RefCircuit(new_instructions)

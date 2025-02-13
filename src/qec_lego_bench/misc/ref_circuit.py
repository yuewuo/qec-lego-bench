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
import functools
from frozendict import frozendict
from frozenlist import FrozenList


@dataclass(frozen=True)
class RefRec:
    instruction: "RefInstruction"
    bias: int

    def __post_init__(self):
        if self.bias < 0:
            raise ValueError("The bias must be a non-negative integer.")

    def abs_index(self, circuit: "RefCircuit") -> int:
        return circuit.rec_to_index[id(self)]

    def rel_index(self, circuit: "RefCircuit", instruction: "RefInstruction") -> int:
        """get the relative rec index before executing the instruction"""
        return (
            circuit.rec_to_index[id(self)]
            - circuit.instruction_to_rec_bias[id(instruction)]
        )

    def __eq__(self, other: "RefInstruction") -> bool:
        return id(self) == id(other)  # avoiding value-based comparison

    def __hash__(self) -> int:
        return hash(id(self))


@dataclass(frozen=True)
class RefInstruction:
    name: str
    targets: tuple[stim.GateTarget | RefRec, ...]
    gate_args: tuple[float, ...]
    tag: str
    recs: FrozenList[RefRec] = field(default_factory=FrozenList)

    @property
    def num_measurements(self) -> int:
        return len(self.recs)

    def index(self, circuit: "RefCircuit") -> int:
        return circuit.instruction_to_index[id(self)]

    def __eq__(self, other: "RefInstruction") -> bool:
        return id(self) == id(other)  # avoiding value-based comparison

    def __hash__(self) -> int:
        return hash(id(self))


@dataclass
class RefIterInfo:
    measurement_indices: dict[int, int]
    # before the current instruction is added to the measurement
    num_measurements: int
    instruction: RefInstruction
    stim_instruction: stim.CircuitInstruction


class RefCircuit:
    def __init__(self, circuit: stim.Circuit | Iterable[RefInstruction] | None = None):
        if circuit is None:
            self.instructions: tuple[RefInstruction, ...] = tuple()
            return
        if not isinstance(circuit, stim.Circuit):
            self.instructions = tuple(circuit)
            self.sanity_check()
            return
        instructions: list[RefInstruction] = []
        recs: list[RefRec] = []
        for instruction in circuit.flattened():
            # rewrite the gate target to absolute measurement indices
            abs_targets: list[stim.GateTarget | RefRec] = []
            for target in instruction.targets_copy():
                if target.is_measurement_record_target:
                    abs_targets.append(recs[target.value])
                else:
                    abs_targets.append(target)
            # construct the instruction
            ref_instruction = RefInstruction(
                name=instruction.name,
                targets=tuple(abs_targets),
                gate_args=tuple(instruction.gate_args_copy()),
                tag=instruction.tag,
            )
            instructions.append(ref_instruction)
            # add the measurement to the measurement list
            for bias in range(instruction.num_measurements):
                reference_rec = RefRec(
                    instruction=ref_instruction,
                    bias=bias,
                )
                ref_instruction.recs.append(reference_rec)
                recs.append(reference_rec)
            ref_instruction.recs.freeze()  # do not allow further edit
        self.instructions = tuple(instructions)
        self.sanity_check()

    def __repr__(self) -> str:
        repr_str = "RefCircuit: {  # not executable\n"
        repr_str += "\n".join("    " + e for e in str(self).splitlines())
        repr_str += "\n}"
        return repr_str

    def __str__(self) -> str:
        # print the circuit in absolute indices; this helps writing test cases
        code_str = ""
        for instruction, stim_instruction in zip(
            self.instructions, self.stim_instructions
        ):
            rec_count: dict[RefRec, int] = {}
            for ref_target in instruction.targets:
                if isinstance(ref_target, RefRec):
                    if ref_target in rec_count:
                        rec_count[ref_target] += 1
                    else:
                        rec_count[ref_target] = 1
            instruction_str = str(stim_instruction)
            # change all the relative indices to absolute indices
            for ref_rec, count in rec_count.items():
                # this count checking is safe because "rec[..]" becomes "rec[..\C"
                # in the tag parameter, and the character "]" cannot appear elsewhere
                relative_index = ref_rec.rel_index(self, instruction)
                assert instruction_str.count(f"rec[{relative_index}]") == count
                instruction_str = instruction_str.replace(
                    f"rec[{relative_index}]", f"abs[{ref_rec.abs_index(self)}]"
                )
            if len(code_str) > 0:
                code_str += "\n"
            code_str += instruction_str
        return code_str

    def __iter__(self) -> Iterator[RefInstruction]:
        for instruction in self.instructions:
            yield instruction

    @functools.cached_property
    def recs(self) -> tuple[RefRec, ...]:
        recs: list[RefRec] = []
        for instruction in self.instructions:
            recs.extend(instruction.recs)
        return tuple(recs)

    @functools.cached_property
    def rec_to_index(self) -> frozendict[int, int]:
        return frozendict(
            {id(ref_rec): index for index, ref_rec in enumerate(self.recs)}
        )

    @functools.cached_property
    def instruction_to_index(self) -> frozendict[int, int]:
        return frozendict(
            {
                id(instruction): index
                for index, instruction in enumerate(self.instructions)
            }
        )

    @functools.cached_property
    def instruction_rec_biases(self) -> tuple[int, ...]:
        rec_bias: int = 0
        rec_biases: list[int] = []
        for instruction in self.instructions:
            rec_biases.append(rec_bias)
            rec_bias += instruction.num_measurements
        return tuple(rec_biases)

    @functools.cached_property
    def instruction_to_rec_bias(self) -> frozendict[int, int]:
        return frozendict(
            {
                id(instruction): bias
                for instruction, bias in zip(
                    self.instructions, self.instruction_rec_biases
                )
            }
        )

    @functools.cached_property
    def detectors(self) -> tuple[RefInstruction, ...]:
        detectors: list[RefInstruction] = []
        for instruction in self.instructions:
            if instruction.name == "DETECTOR":
                detectors.append(instruction)
        return tuple(detectors)

    @functools.cached_property
    def detector_to_index(self) -> frozendict[int, int]:
        return frozendict(
            {id(detector): index for index, detector in enumerate(self.detectors)}
        )

    @functools.cached_property
    def stim_instructions(self) -> tuple[stim.CircuitInstruction, ...]:
        stim_instructions: list[stim.CircuitInstruction] = []
        for instruction in self.instructions:
            relative_targets = []
            for ref_target in instruction.targets:
                if isinstance(ref_target, RefRec):
                    relative_targets.append(
                        stim.target_rec(ref_target.rel_index(self, instruction))
                    )
                else:
                    relative_targets.append(ref_target)
            stim_instructions.append(
                stim.CircuitInstruction(
                    name=instruction.name,
                    targets=relative_targets,
                    gate_args=instruction.gate_args,
                    tag=instruction.tag,
                )
            )
        return tuple(stim_instructions)

    def circuit(self) -> stim.Circuit:
        circuit = stim.Circuit()
        for stim_instruction in self.stim_instructions:
            circuit.append(stim_instruction)
        return circuit

    def __getitem__(self, key: slice) -> "RefInstruction | RefCircuit":
        if isinstance(key, int):
            return self.instructions[key]
        elif isinstance(key, slice):
            return RefCircuit(self.instructions[key])
        else:
            raise TypeError("Invalid key type")

    def __add__(self, other: "RefCircuit | RefInstruction") -> "RefCircuit":
        if isinstance(other, RefInstruction):
            return RefCircuit([*self.instructions, other])
        elif isinstance(other, RefCircuit):
            return RefCircuit([*self.instructions, *other.instructions])
        else:
            raise NotImplemented()

    def __radd__(self, other: "RefCircuit | RefInstruction") -> "RefCircuit":
        if isinstance(other, RefInstruction):
            return RefCircuit([other, *self.instructions])
        elif isinstance(other, RefCircuit):
            return RefCircuit([*other.instructions, *self.instructions])
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
        rec_index_of: dict[int, int] = {
            id(ref_rec): index for index, ref_rec in enumerate(self.recs)
        }
        assert len(rec_index_of) == len(self.recs), "has duplicate RefRec object"
        rec_hashes = set(hash(rec) for rec in self.recs)
        assert len(rec_hashes) == len(self.recs), "hash conflict"
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
            for ref_rec in instruction.recs:
                assert id(ref_rec.instruction) == id(instruction)  # must refer itself
                previous_rec_set.add(id(ref_rec))
            previous_instruction_set.add(id(instruction))
        # check that the number of measurements is correct
        for instruction, stim_instruction in zip(
            self.instructions, self.stim_instructions
        ):
            assert stim_instruction.num_measurements == instruction.num_measurements

    def clone(self) -> "RefCircuit":
        """
        make a deep copy of the RefCircuit object, creating branch new instructions
        with different ids, but keeping the circuit the same
        """
        new_instructions: list[RefInstruction] = []
        new_rec: list[RefRec] = []
        for instruction in self.instructions:
            new_instruction = RefInstruction(
                name=instruction.name,
                targets=tuple(
                    (
                        new_rec[self.rec_to_index[id(target)]]
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
                new_instruction.recs.append(reference_rec)
                new_rec.append(reference_rec)
            new_instruction.recs.freeze()  # do not allow further edit
            new_instructions.append(new_instruction)
        return RefCircuit(new_instructions)

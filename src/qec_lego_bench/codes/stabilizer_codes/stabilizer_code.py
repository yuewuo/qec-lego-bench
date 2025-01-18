from abc import ABC, abstractmethod
from qec_lego_bench.codes.code import Code
import stim


class StabilizerCode(Code, ABC):

    @property
    @abstractmethod
    def n(self) -> int: ...

    @property
    @abstractmethod
    def stabilizers(self) -> list[stim.PauliString]: ...

    def init_logical_operators(self):
        # https://quantumcomputing.stackexchange.com/questions/37812/how-to-find-a-set-of-independent-logical-operators-for-a-stabilizer-code-with-st
        completed_tableau = stim.Tableau.from_stabilizers(
            self.stabilizers,
            allow_redundant=True,
            allow_underconstrained=True,
        )
        self._logical_operators = []
        for k in range(len(completed_tableau))[::-1]:
            z = completed_tableau.z_output(k)
            if z in self.stabilizers:
                break
            x = completed_tableau.x_output(k)
            self._logical_operators.append((x, z))

    def init_circuit(self):
        c = stim.Circuit()
        # add qubit coordinates
        for qubit_index, coordinate in enumerate(self.qubit_coordinates):
            if coordinate is not None:
                c.append("QUBIT_COORDS", qubit_index, coordinate)
        # prepare the qubits in some random stabilizer states and logical state
        for stabilizer in self.stabilizers:
            assert len(stabilizer) <= self.n
            c.append("MPP", stim.target_combined_paulis(stabilizer))
        for logical_x, logical_z in self.logical_operators:
            assert len(logical_x) <= self.n
            assert len(logical_z) <= self.n
            logical = logical_x if self.prepare_logical_x_instead_of_z else logical_z
            c.append("MPP", stim.target_combined_paulis(logical))
        bias = len(self.stabilizers) + len(self.logical_operators)
        # add errors at TICK positions
        c.append("TICK")
        c.append("SHIFT_COORDS", (), (0, 0, 1))
        # add the detectors by measuring the stabilizers again and compare the difference
        for stabilizer, coordinates in zip(
            self.stabilizers, self.stabilizer_coordinates
        ):
            c.append("MPP", stim.target_combined_paulis(stabilizer))
            c.append(
                "DETECTOR",
                [stim.target_rec(-1), stim.target_rec(-1 - bias)],
                coordinates,
            )
        # check logical errors by measuring the logical operators
        for logical_index, (logical_x, logical_z) in enumerate(self.logical_operators):
            logical = logical_x if self.prepare_logical_x_instead_of_z else logical_z
            c.append("MPP", stim.target_combined_paulis(logical))
            c.append(
                "OBSERVABLE_INCLUDE",
                [stim.target_rec(-1), stim.target_rec(-1 - bias)],
                logical_index,
            )
        self._circuit = c

    def __init__(self):
        # construct logical observables to check logical errors
        self.init_logical_operators()
        # construct the circuit of the code
        self.init_circuit()
        # call the parent constructor
        super().__init__()

    @property
    def logical_operators(self) -> list[tuple[stim.PauliString]]:
        return self._logical_operators

    @property
    def circuit(self) -> stim.Circuit:
        return self._circuit

    @property
    def qubit_coordinates(self) -> list[tuple[float, float, float] | None]:
        return [None] * self.n

    @property
    def stabilizer_coordinates(self) -> list[tuple[float, float, float] | None]:
        return [None] * len(self.stabilizers)

    @property
    def prepare_logical_x_instead_of_z(self) -> bool:
        return False

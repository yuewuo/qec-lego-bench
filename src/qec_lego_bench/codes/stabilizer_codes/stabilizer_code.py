from abc import ABC, abstractmethod
from qec_lego_bench.codes.code import Code
import stim
from galois import GF2
import numpy as np


class StabilizerCode(Code, ABC):

    @property
    @abstractmethod
    def stabilizers(self) -> list[stim.PauliString]: ...

    def stabilizer_init_logical_operators(self):
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

    def __init__(self):
        # construct logical observables to check logical errors
        self.stabilizer_init_logical_operators()
        # construct the circuit of the code

    @property
    def logical_operators(self) -> list[tuple[stim.PauliString]]:
        return self._logical_operators

    @property
    def circuit(self) -> stim.Circuit:
        return self._circuit

from qec_lego_bench.codes.stabilizer_codes import StabilizerCode
from abc import ABC, abstractmethod
from galois.typing import ArrayLike
import stim
from galois import GF2
import numpy as np


class CSSCode(StabilizerCode, ABC):

    @property
    @abstractmethod
    def H_X(self) -> ArrayLike: ...

    @property
    @abstractmethod
    def H_Z(self) -> ArrayLike: ...

    def css_init_stabilizers(self):
        assert (self.H_X @ self.H_Z.T == 0).all(), "X and Z checks must commute"
        self._stabilizers = []
        for t, matrix in [("X", self.H_X), ("Z", self.H_Z)]:
            for line in matrix:
                self._stabilizers.append(
                    stim.PauliString([t if e == 1 else "I" for e in line])
                )

    @property
    def stabilizers(self) -> list[stim.PauliString]:
        return self._stabilizers

    @property
    def x_stabilizer_coordinates(self) -> list[tuple[float, float, float] | None]:
        return [None] * len(self.H_X.shape[1])

    @property
    def z_stabilizer_coordinates(self) -> list[tuple[float, float, float] | None]:
        return [None] * len(self.H_Z.shape[1])

    @property
    def stabilizer_coordinates(self) -> list[tuple[float, float, float] | None]:
        return self.x_stabilizer_coordinates + self.z_stabilizer_coordinates

    def __init__(self):
        self.css_init_stabilizers()
        super().__init__()

        self.L_X, self.L_Z = construct_logical_checks(self.logical_operators)
        assert (self.H_X @ self.L_Z.T == 0).all()
        assert (self.H_Z @ self.L_X.T == 0).all()


def construct_logical_checks(
    logical_operators: list[tuple[stim.PauliString, stim.PauliString]],
) -> tuple[ArrayLike, ArrayLike]:
    height = len(logical_operators)
    width = len(logical_operators[0][0])
    L_X = GF2(np.zeros((height, width), dtype=np.uint8))
    L_Z = GF2(np.zeros((height, width), dtype=np.uint8))
    for idx, (l_x, l_z) in enumerate(logical_operators):
        for t, l, L in [("X", l_x, L_X), ("Z", l_z, L_Z)]:
            indices = l.pauli_indices(t)
            assert indices == l.pauli_indices(), "should not include other Pauli types"
            L[idx][indices] = 1
    return L_X, L_Z

from qec_lego_bench.codes.stabilizer_codes.css_codes import CSSCode
from dataclasses import dataclass
from galois import GF2
import numpy as np
from galois.typing import ArrayLike
from qec_lego_bench.cli.codes import code_cli


BBExpr = tuple[int, int, int]


def index_of_d(d: int, i: int, j: int) -> int:
    assert i <= d
    assert j <= d
    return i * d + j


@code_cli("RotatedSurfaceCode", "css_rsc")
@dataclass
class RotatedSurfaceCode(CSSCode):
    d: int

    @property
    def n(self) -> int:
        return self.d * self.d

    def __post_init__(self) -> None:
        n = self.n
        d = self.d
        assert d % 2 == 1
        s = (n - 1) // 2  # how many stabilizers of each type
        sr = (d + 1) // 2  # how many stabilizers in a row

        def index_of(i: int, j: int) -> int:
            assert 0 <= i < d
            assert 0 <= j < d
            return i * d + j

        def s_index_of(si: int, sj: int) -> int:
            assert 0 <= si < d - 1
            assert 0 <= sj < sr
            return si * sr + sj

        self._H_X = GF2(np.zeros((s, n), dtype=np.uint8))
        self._H_Z = GF2(np.zeros((s, n), dtype=np.uint8))
        self._qubit_coordinates = [None] * n
        self._x_stabilizer_coordinates = [None] * s
        self._z_stabilizer_coordinates = [None] * s
        for i in range(d):
            for j in range(d):
                self._qubit_coordinates[index_of(i, j)] = (i, j, 0)
        for si in range(d - 1):
            for sj in range(sr):
                stab_index = s_index_of(si, sj)
                x_i_center = si + 0.5
                x_j_center = 2 * sj + (-0.5 if si % 2 == 0 else 0.5)
                # X stabilizers
                self._x_stabilizer_coordinates[stab_index] = (
                    x_i_center,
                    x_j_center,
                    0,
                )
                for qi in [round(x_i_center - 0.5), round(x_i_center + 0.5)]:
                    for qj in [round(x_j_center - 0.5), round(x_j_center + 0.5)]:
                        if 0 <= qi < d and 0 <= qj < d:
                            self._H_X[stab_index, index_of(qi, qj)] = 1
                # Z stabilizers are rotated by 90 degrees
                z_i_center = x_j_center
                z_j_center = d - 1 - x_i_center
                self._z_stabilizer_coordinates[stab_index] = (
                    z_i_center,
                    z_j_center,
                    0,
                )
                for qi in [round(z_i_center - 0.5), round(z_i_center + 0.5)]:
                    for qj in [round(z_j_center - 0.5), round(z_j_center + 0.5)]:
                        if 0 <= qi < d and 0 <= qj < d:
                            self._H_Z[stab_index, index_of(qi, qj)] = 1

        super().__init__()

        assert len(self.logical_operators) == 1

    @property
    def H_X(self) -> ArrayLike:
        return self._H_X

    @property
    def H_Z(self) -> ArrayLike:
        return self._H_Z

    @property
    def qubit_coordinates(self) -> list[tuple[float, float, float] | None]:
        return self._qubit_coordinates

    @property
    def x_stabilizer_coordinates(self) -> list[tuple[float, float, float] | None]:
        return self._x_stabilizer_coordinates

    @property
    def z_stabilizer_coordinates(self) -> list[tuple[float, float, float] | None]:
        return self._z_stabilizer_coordinates

from qec_lego_bench.codes.stabilizer_codes.css_codes import CSSCode, Coordinates
from dataclasses import dataclass
from galois import GF2
import numpy as np
from qec_lego_bench.cli.codes import code_cli


@code_cli("TriangularColorCode", "css_color")
@dataclass
class TriangularColorCode(CSSCode):
    d: int

    @property
    def n(self) -> int:
        d = self.d
        return d * (d + 1) // 2 + ((d - 1) // 2) ** 2

    def __post_init__(self) -> None:
        n = self.n
        d = self.d
        assert d % 2 == 1
        s = (n - 1) // 2  # how many stabilizers of each type

        self._rows = 3 * (d - 1) // 2 + 1
        self._columns = 2 * d - 1

        self._qubit_coordinates: Coordinates = []
        self._qubit_coordinates_to_index: dict[tuple[int, int], int] = {}

        def add_data_qubit(c: int, r: int):
            idx = len(self._qubit_coordinates)
            self._qubit_coordinates_to_index[(r, c)] = idx
            self._qubit_coordinates.append((r, c, 0))

        self._H_X = GF2(np.zeros((s, n), dtype=np.uint8))
        self._H_Z = GF2(np.zeros((s, n), dtype=np.uint8))
        self._x_stabilizer_coordinates: Coordinates = []
        self._z_stabilizer_coordinates: Coordinates = []
        self._x_stabilizer_coordinates_to_index: dict[tuple[int, int], int] = {}
        self._z_stabilizer_coordinates_to_index: dict[tuple[int, int], int] = {}

        def add_x_stabilizer(c: int, r: int) -> int:
            idx = len(self._x_stabilizer_coordinates)
            self._x_stabilizer_coordinates_to_index[(r, c)] = idx
            self._x_stabilizer_coordinates.append((r, c, 0))
            return idx

        def add_z_stabilizer(c: int, r: int) -> int:
            idx = len(self._z_stabilizer_coordinates)
            self._z_stabilizer_coordinates_to_index[(r, c)] = idx
            self._z_stabilizer_coordinates.append((r, c, 0))
            return idx

        # first add all data qubits
        for r in range(self._rows):
            for c in self._range_for_row(r):
                if self._is_data_qubit(r, c):
                    add_data_qubit(c, r)

        # then add all stabilizers
        for r in range(self._rows):
            for c in self._range_for_row(r):
                if self._is_z_stabilizer(r, c):
                    z_idx = add_z_stabilizer(c, r)
                    for qubit_idx in self._z_stabilizer_data_qubit_indices(r, c):
                        self._H_Z[z_idx, qubit_idx] = 1
                elif self._is_x_stabilizer(r, c):
                    x_idx = add_x_stabilizer(c, r)
                    for qubit_idx in self._x_stabilizer_data_qubit_indices(r, c):
                        self._H_X[x_idx, qubit_idx] = 1

        super().__init__()

        assert len(self.logical_operators) == 1

    def _range_for_row(self, r: int) -> range:
        cr = r // 3
        start = 2 * cr + (0 if r % 3 == 0 else 1)
        length = self._columns - 4 * cr - (r % 3)
        return range(start, start + length)

    def _is_any_qubit(self, r: int, c: int) -> bool:
        if r < 0 or r >= self._rows:
            return False
        return c in self._range_for_row(r)

    def _is_data_qubit(self, r: int, c: int) -> bool:
        if not self._is_any_qubit(r, c):
            return False
        return (c % 4) in ([0, 3] if r % 2 == 0 else [1, 2])

    def _is_z_stabilizer(self, r: int, c: int) -> bool:
        if not self._is_any_qubit(r, c):
            return False
        return (c % 4) == (1 if r % 2 == 0 else 3)

    def _is_x_stabilizer(self, r: int, c: int) -> bool:
        if not self._is_any_qubit(r, c):
            return False
        return (c % 4) == (2 if r % 2 == 0 else 0)

    def _z_stabilizer_data_qubit_indices(self, r: int, c: int) -> list[int]:
        candidates = [(-1, 0), (-1, 1), (0, -1), (0, 2), (1, 0), (1, 1)]
        indices = []
        for dr, dc in candidates:
            if self._is_data_qubit(r + dr, c + dc):
                indices.append(self._qubit_coordinates_to_index[(r + dr, c + dc)])
        return indices

    def _x_stabilizer_data_qubit_indices(self, r: int, c: int) -> list[int]:
        candidates = [(-1, -1), (-1, 0), (0, -2), (0, 1), (1, -1), (1, 0)]
        indices = []
        for dr, dc in candidates:
            if self._is_data_qubit(r + dr, c + dc):
                indices.append(self._qubit_coordinates_to_index[(r + dr, c + dc)])
        return indices

    @property
    def H_X(self) -> np.ndarray:
        return self._H_X

    @property
    def H_Z(self) -> np.ndarray:
        return self._H_Z

    @property
    def qubit_coordinates(self) -> Coordinates:
        return self._qubit_coordinates

    @property
    def x_stabilizer_coordinates(self) -> Coordinates:
        return self._x_stabilizer_coordinates

    @property
    def z_stabilizer_coordinates(self) -> Coordinates:
        return self._z_stabilizer_coordinates

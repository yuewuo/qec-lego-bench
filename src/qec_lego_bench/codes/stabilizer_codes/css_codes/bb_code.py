from qec_lego_bench.codes.code import Code
from qec_lego_bench.codes.stabilizer_codes.css_codes import CSSCode
from stim import Circuit
from dataclasses import dataclass
import stim
from galois import GF2
import numpy as np
from galois.typing import ArrayLike
from itertools import chain
import mwpf
from qec_lego_bench.cli.codes import code_cli


BBExpr = tuple[int, int, int]


@dataclass
class BBConfig:

    def __str__(self) -> str:
        n, k, d = self.nkd
        str_of = lambda bb_expr: "+".join(
            [
                "1" if exp == 0 else (var if exp == 1 else f"{var}^{{{exp}}}")
                for (var, exp) in bb_expr
            ]
        )
        d_str = ("\\le" if self.unsure_d else "") + str(d)
        return f"[[{n}, {k}, {d_str}]]: l={self.l}, m={self.m}, A={str_of(self.A)}, B={str_of(self.B)}"

    @property
    def n(self) -> int:
        return 2 * self.l * self.m


@dataclass
class BBCode(Code):
    n: int
    k: int
    d: int
    l: int
    m: int
    a: BBExpr
    b: BBExpr
    unsure_d: bool = False

    def __post_init__(self):
        # sanity check
        n, k, d = self.nkd
        assert n == 2 * self.l * self.m
        for bb_expr in [self.a, self.b]:
            for exp in bb_expr:
                assert exp >= 0
        # construct the matrices
        lm = self.l * self.m

        self.matrix_A: ArrayLike = gf2_zeros(shape=(lm, lm))
        self.matrix_A += x_matrix(self.l, self.m, self.a[0])
        self.matrix_A += y_matrix(self.l, self.m, self.a[1])
        self.matrix_A += y_matrix(self.l, self.m, self.a[2])

        self.matrix_B: ArrayLike = gf2_zeros(shape=(lm, lm))
        self.matrix_B += y_matrix(self.l, self.m, self.b[0])
        self.matrix_B += x_matrix(self.l, self.m, self.b[1])
        self.matrix_B += x_matrix(self.l, self.m, self.b[2])

        assert (self.matrix_A @ self.matrix_B == self.matrix_B @ self.matrix_A).all()
        self.H_X = np.concatenate((self.matrix_A, self.matrix_B), axis=1)
        self.H_Z = np.concatenate((self.matrix_B.T, self.matrix_A.T), axis=1)

        assert k_of(self.matrix_A, self.matrix_B) == k

        super().__init__()

        # assert k value
        assert (
            2 * lm - np.linalg.matrix_rank(self.H_X) - np.linalg.matrix_rank(self.H_Z)
            == k
        )
        assert len(self.logical_operators) == k

    def __init__(self):
        c = Circuit()

        c.append("MPP", [[stim.target_x(0), stim.target_y(1), stim.target_z(2)]])
        print(self.c)
        self.c = c
        print(c.num_measurements)

    def circuit(self) -> Circuit:
        return self.circuit


@code_cli("BBCode")
class BBCodeCli:
    def __init__(self, p: float, d: int):
        pass


gf2_zeros = lambda shape: GF2(np.zeros(shape, dtype=np.uint8))
gf2_eye = lambda N: GF2(np.eye(N, dtype=np.uint8))


def x_matrix(l: int, m: int, exp: int):
    S = gf2_zeros(shape=(l, l))
    for i in range(l):
        S[i, (i + exp) % l] = 1
    return np.kron(S, gf2_eye(m))


def y_matrix(l: int, m: int, exp: int):
    S = gf2_zeros(shape=(m, m))
    for i in range(m):
        S[i, (i + exp) % m] = 1
    return np.kron(gf2_eye(l), S)


def k_of(matrix_A: ArrayLike, matrix_B: ArrayLike) -> int:
    gf2 = mwpf.TightMatrix()
    for i in range(matrix_A.shape[1]):
        gf2.add_tight_variable(i)
    for line_idx, line in enumerate(chain(matrix_A, matrix_B)):
        gf2.add_constraint(line_idx, np.nonzero(line)[0], False)
    echelon = mwpf.EchelonMatrix(gf2)
    return 2 * (matrix_A.shape[1] - echelon.rows)

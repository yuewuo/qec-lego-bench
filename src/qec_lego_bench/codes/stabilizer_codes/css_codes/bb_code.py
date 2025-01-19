from qec_lego_bench.codes.stabilizer_codes.css_codes import CSSCode
from dataclasses import dataclass
from galois import GF2
import numpy as np
from galois.typing import ArrayLike
from qec_lego_bench.cli.codes import code_cli


BBExpr = tuple[int, int, int]


@dataclass
class BBCode(CSSCode):
    nkd: tuple[int, int, int]
    l: int
    m: int
    a: BBExpr
    b: BBExpr
    unsure_d: bool = False

    @property
    def n(self) -> int:
        return self.nkd[0]

    def __post_init__(self) -> None:
        # sanity check
        n, k, d = self.nkd
        assert n == 2 * self.l * self.m
        for bb_expr in [self.a, self.b]:
            for exp in bb_expr:
                assert exp >= 0
        # construct the matrices
        lm = self.l * self.m

        self.matrix_A: ArrayLike = GF2(np.zeros((lm, lm), dtype=np.uint8))
        self.matrix_A += x_matrix(self.l, self.m, self.a[0])
        self.matrix_A += y_matrix(self.l, self.m, self.a[1])
        self.matrix_A += y_matrix(self.l, self.m, self.a[2])

        self.matrix_B: ArrayLike = GF2(np.zeros((lm, lm), dtype=np.uint8))
        self.matrix_B += y_matrix(self.l, self.m, self.b[0])
        self.matrix_B += x_matrix(self.l, self.m, self.b[1])
        self.matrix_B += x_matrix(self.l, self.m, self.b[2])

        assert (self.matrix_A @ self.matrix_B == self.matrix_B @ self.matrix_A).all()
        self._H_X = np.concatenate((self.matrix_A, self.matrix_B), axis=1)
        self._H_Z = np.concatenate((self.matrix_B.T, self.matrix_A.T), axis=1)

        super().__init__()

        # assert k value using multiple equivalent methods
        assert (
            2
            * (
                self.matrix_A.shape[1]
                - np.linalg.matrix_rank(
                    np.concatenate((self.matrix_A, self.matrix_B), axis=0)
                )
            )
            == k
        )
        assert (
            2 * lm - np.linalg.matrix_rank(self.H_X) - np.linalg.matrix_rank(self.H_Z)  # type: ignore
            == k
        )
        assert len(self.logical_operators) == k

    @property
    def H_X(self) -> ArrayLike:
        return self._H_X

    @property
    def H_Z(self) -> ArrayLike:
        return self._H_Z

    def __str__(self) -> str:
        n, k, d = self.nkd
        pow_of = lambda var, exp: (
            "1" if exp == 0 else var if exp == 1 else f"{var}^{exp}"
        )
        str_A = (
            f"{pow_of('x',self.a[0])}+{pow_of('y',self.a[1])}+{pow_of('y',self.a[2])}"
        )
        str_B = (
            f"{pow_of('y',self.b[0])}+{pow_of('x',self.b[1])}+{pow_of('x',self.b[2])}"
        )
        d_str = ("\\le" if self.unsure_d else "") + str(d)
        return f"[[{n}, {k}, {d_str}]]: l={self.l}, m={self.m}, A={str_A}, B={str_B}"


bb_code_params = [
    dict(
        nkd=(72, 12, 6),
        l=6,
        m=6,
        a=(3, 1, 2),
        b=(3, 1, 2),
    ),
    dict(
        nkd=(90, 8, 10),
        l=15,
        m=3,
        a=(9, 1, 2),
        b=(0, 2, 7),
    ),
    dict(
        nkd=(108, 8, 10),
        l=9,
        m=6,
        a=(3, 1, 2),
        b=(3, 1, 2),
    ),
    dict(
        nkd=(144, 12, 12),
        l=12,
        m=6,
        a=(3, 1, 2),
        b=(3, 1, 2),
    ),
    dict(
        n=(288, 12, 18),
        l=12,
        m=12,
        a=(3, 2, 7),
        b=(3, 1, 2),
    ),
]


@code_cli("BBCode", "bb")
def bb_code_cli(n: int, k: int, d: int) -> BBCode:
    for params in bb_code_params:
        if params["nkd"] == (n, k, d):
            return BBCode(**params)  # type: ignore
    raise ValueError(f"no BBCode with n={n}, k={k}, d={d}")


def x_matrix(l: int, m: int, exp: int):
    S = GF2(np.zeros((l, l), dtype=np.uint8))
    for i in range(l):
        S[i, (i + exp) % l] = 1
    return np.kron(S, GF2(np.eye(m, dtype=np.uint8)))


def y_matrix(l: int, m: int, exp: int):
    S = GF2(np.zeros((m, m), dtype=np.uint8))
    for i in range(m):
        S[i, (i + exp) % m] = 1
    return np.kron(GF2(np.eye(l, dtype=np.uint8)), S)

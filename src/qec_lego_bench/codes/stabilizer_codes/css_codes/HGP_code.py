from qec_lego_bench.codes.stabilizer_codes.css_codes import CSSCode
from dataclasses import dataclass
from galois import GF2
import numpy as np
from galois.typing import ArrayLike
from qec_lego_bench.cli.codes import code_cli


@dataclass
class HGPCode(CSSCode):

    @property
    def n(self) -> int:
        return 625

    def __post_init__(self) -> None:
        self.k = 25

        # construct HX and HZ
        # Classical parity check matrix (see Huang et al. 2023).
        H1 = GF2(
            np.array(
                [
                    [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
                    [0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
                    [0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
                    [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0],
                    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
                    [0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
                    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
                    [1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
                    [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0],
                ],
                dtype=np.uint8,
            )
        )

        H2 = H1

        # Given that H1 has dims r1 x n1, and H2 has dims r2 x n2, then the quantum check matrices are
        r1 = H1.shape[0]
        n1 = H1.shape[1]
        r2 = H2.shape[0]
        n2 = H2.shape[1]

        Hx = np.concatenate(
            (
                np.kron(np.transpose(H1), GF2(np.identity(r2, dtype=np.uint8))),
                np.kron(GF2(np.identity(n1, dtype=np.uint8)), H2),
            ),
            axis=1,
        )

        Hz = np.concatenate(
            (
                np.kron(GF2(np.identity(r1, dtype=np.uint8)), np.transpose(H2)),
                np.kron(H1, GF2(np.identity(n2, dtype=np.uint8))),
            ),
            axis=1,
        )

        self._H_X = Hx
        self._H_Z = Hz

        super().__init__()

        # assert k value using multiple equivalent methods
        assert len(self.logical_operators) == self.k

    @property
    def H_X(self) -> np.ndarray:
        return self._H_X

    @property
    def H_Z(self) -> np.ndarray:
        return self._H_Z


@code_cli("HGPCode", "hgp")
def HGP_code_cli() -> HGPCode:
    return HGPCode()

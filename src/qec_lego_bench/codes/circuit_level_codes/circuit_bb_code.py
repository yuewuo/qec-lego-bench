"""
https://github.com/gongaa/SlidingWindowDecoder/blob/7fd1b8edb596f076f68cc55208fe193169c23fcc/src/build_circuit.py

MIT License

Copyright (c) 2024 Anqi Gong

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from qec_lego_bench.codes.stabilizer_codes.css_codes.bb_code import (
    BBCode,
    bb_code_params,
)
from dataclasses import dataclass
from galois import GF2
import numpy as np
from galois.typing import ArrayLike
from qec_lego_bench.cli.codes import code_cli
from stim import Circuit
from functools import cached_property
from typing import Sequence


def nnz(m: np.ndarray) -> np.ndarray:
    a, b = m.nonzero()
    return b[np.argsort(a)]


@dataclass
class CircuitBBCode(BBCode):
    p: float | None = None
    num_repeat: int = 1

    p_after_clifford_depolarization: float | None = None
    p_after_reset_flip_probability: float | None = None
    p_before_measure_flip_probability: float | None = None
    p_before_round_data_depolarization: float | None = None

    z_basis: bool = True
    use_both: bool = False
    HZH: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        assert self.n % 2 == 0
        if self.p is None:
            self.p = 0.0
        if self.p_after_clifford_depolarization is None:
            self.p_after_clifford_depolarization = self.p
        if self.p_after_reset_flip_probability is None:
            self.p_after_reset_flip_probability = self.p
        if self.p_before_measure_flip_probability is None:
            self.p_before_measure_flip_probability = self.p
        if self.p_before_round_data_depolarization is None:
            self.p_before_round_data_depolarization = self.p

    def qX(self, i: int) -> int:
        assert i < self.n // 2
        return i

    def qL(self, i: int) -> int:
        assert i < self.n // 2
        return i + (self.n // 2)

    def qR(self, i: int) -> int:
        assert i < self.n // 2
        return i + self.n

    def qZ(self, i: int) -> int:
        assert i < self.n // 2
        return i + (self.n // 2) * 3

    @cached_property
    def circuit(self) -> Circuit:
        """
        The circuit according to Table 5 in High-threshold and low-overhead fault-tolerant quantum memory
        """
        circuit = Circuit()

        A1, A2, A3 = nnz(self.A1), nnz(self.A2), nnz(self.A3)
        B1, B2, B3 = nnz(self.B1), nnz(self.B2), nnz(self.B3)

        A1_T, A2_T, A3_T = nnz(self.A1.T), nnz(self.A2.T), nnz(self.A3.T)
        B1_T, B2_T, B3_T = nnz(self.B1.T), nnz(self.B2.T), nnz(self.B3.T)

        n = self.n

        detector_circuit_str = ""
        for i in range(n // 2):
            detector_circuit_str += f"DETECTOR rec[{-n//2+i}]\n"
        detector_circuit = Circuit(detector_circuit_str)

        detector_repeat_circuit_str = ""
        for i in range(n // 2):
            detector_repeat_circuit_str += f"DETECTOR rec[{-n//2+i}] rec[{-n-n//2+i}]\n"
        detector_repeat_circuit = Circuit(detector_repeat_circuit_str)

        data_qubits = [self.qL(i) for i in range(n // 2)] + [
            self.qR(i) for i in range(n // 2)
        ]

        def append_blocks(circuit, repeat=False):
            # Round 1
            if repeat:
                for i in range(n // 2):
                    # measurement preparation errors
                    circuit.append(
                        "X_ERROR", self.qZ(i), self.p_after_reset_flip_probability
                    )
                    if self.HZH:
                        circuit.append(
                            "X_ERROR",
                            self.qX(i),
                            self.p_after_reset_flip_probability,
                        )
                        circuit.append("H", [self.qX(i)])
                        circuit.append(
                            "DEPOLARIZE1",
                            self.qX(i),
                            self.p_after_clifford_depolarization,
                        )
                    else:
                        circuit.append(
                            "Z_ERROR",
                            self.qX(i),
                            self.p_after_reset_flip_probability,
                        )
                    # identity gate on R data
                    circuit.append(
                        "DEPOLARIZE1",
                        self.qR(i),
                        self.p_before_round_data_depolarization,
                    )
            else:
                for i in range(n // 2):
                    circuit.append("H", [self.qX(i)])
                    if self.HZH:
                        circuit.append(
                            "DEPOLARIZE1",
                            self.qX(i),
                            self.p_after_clifford_depolarization,
                        )

            for i in range(n // 2):
                # CNOTs from R data to to Z-checks
                circuit.append("CNOT", [self.qR(A1_T[i]), self.qZ(i)])
                circuit.append(
                    "DEPOLARIZE2",
                    [self.qR(A1_T[i]), self.qZ(i)],
                    self.p_after_clifford_depolarization,
                )
                # identity gate on L data
                circuit.append(
                    "DEPOLARIZE1", self.qL(i), self.p_before_round_data_depolarization
                )

            # tick
            circuit.append("TICK")

            # Round 2
            for i in range(n // 2):
                # CNOTs from X-checks to L data
                circuit.append("CNOT", [self.qX(i), self.qL(A2[i])])
                circuit.append(
                    "DEPOLARIZE2",
                    [self.qX(i), self.qL(A2[i])],
                    self.p_after_clifford_depolarization,
                )
                # CNOTs from R data to Z-checks
                circuit.append("CNOT", [self.qR(A3_T[i]), self.qZ(i)])
                circuit.append(
                    "DEPOLARIZE2",
                    [self.qR(A3_T[i]), self.qZ(i)],
                    self.p_after_clifford_depolarization,
                )

            # tick
            circuit.append("TICK")

            # Round 3
            for i in range(n // 2):
                # CNOTs from X-checks to R data
                circuit.append("CNOT", [self.qX(i), self.qR(B2[i])])
                circuit.append(
                    "DEPOLARIZE2",
                    [self.qX(i), self.qR(B2[i])],
                    self.p_after_clifford_depolarization,
                )
                # CNOTs from L data to Z-checks
                circuit.append("CNOT", [self.qL(B1_T[i]), self.qZ(i)])
                circuit.append(
                    "DEPOLARIZE2",
                    [self.qL(B1_T[i]), self.qZ(i)],
                    self.p_after_clifford_depolarization,
                )

            # tick
            circuit.append("TICK")

            # Round 4
            for i in range(n // 2):
                # CNOTs from X-checks to R data
                circuit.append("CNOT", [self.qX(i), self.qR(B1[i])])
                circuit.append(
                    "DEPOLARIZE2",
                    [self.qX(i), self.qR(B1[i])],
                    self.p_after_clifford_depolarization,
                )
                # CNOTs from L data to Z-checks
                circuit.append("CNOT", [self.qL(B2_T[i]), self.qZ(i)])
                circuit.append(
                    "DEPOLARIZE2",
                    [self.qL(B2_T[i]), self.qZ(i)],
                    self.p_after_clifford_depolarization,
                )

            # tick
            circuit.append("TICK")

            # Round 5
            for i in range(n // 2):
                # CNOTs from X-checks to R data
                circuit.append("CNOT", [self.qX(i), self.qR(B3[i])])
                circuit.append(
                    "DEPOLARIZE2",
                    [self.qX(i), self.qR(B3[i])],
                    self.p_after_clifford_depolarization,
                )
                # CNOTs from L data to Z-checks
                circuit.append("CNOT", [self.qL(B3_T[i]), self.qZ(i)])
                circuit.append(
                    "DEPOLARIZE2",
                    [self.qL(B3_T[i]), self.qZ(i)],
                    self.p_after_clifford_depolarization,
                )

            # tick
            circuit.append("TICK")

            # Round 6
            for i in range(n // 2):
                # CNOTs from X-checks to L data
                circuit.append("CNOT", [self.qX(i), self.qL(A1[i])])
                circuit.append(
                    "DEPOLARIZE2",
                    [self.qX(i), self.qL(A1[i])],
                    self.p_after_clifford_depolarization,
                )
                # CNOTs from R data to Z-checks
                circuit.append("CNOT", [self.qR(A2_T[i]), self.qZ(i)])
                circuit.append(
                    "DEPOLARIZE2",
                    [self.qR(A2_T[i]), self.qZ(i)],
                    self.p_after_clifford_depolarization,
                )

            # tick
            circuit.append("TICK")

            # Round 7
            for i in range(n // 2):
                # CNOTs from X-checks to L data
                circuit.append("CNOT", [self.qX(i), self.qL(A3[i])])
                circuit.append(
                    "DEPOLARIZE2",
                    [self.qX(i), self.qL(A3[i])],
                    self.p_after_clifford_depolarization,
                )
                # Measure Z-checks
                circuit.append(
                    "X_ERROR", self.qZ(i), self.p_before_measure_flip_probability
                )
                circuit.append("MR", [self.qZ(i)])
                # identity gates on R data, moved to beginning of the round
                # circuit.append("DEPOLARIZE1", self.qR(i), self.p_before_round_data_depolarization)

            # Z check detectors
            if self.z_basis:
                if repeat:
                    circuit += detector_repeat_circuit
                else:
                    circuit += detector_circuit
            elif self.use_both and repeat:
                circuit += detector_repeat_circuit

            # tick
            circuit.append("TICK")

            # Round 8
            for i in range(n // 2):
                if self.HZH:
                    circuit.append("H", [self.qX(i)])
                    circuit.append(
                        "DEPOLARIZE1",
                        self.qX(i),
                        self.p_after_clifford_depolarization,
                    )
                    circuit.append(
                        "X_ERROR", self.qX(i), self.p_before_measure_flip_probability
                    )
                    circuit.append("MR", [self.qX(i)])
                else:
                    circuit.append(
                        "Z_ERROR", self.qX(i), self.p_before_measure_flip_probability
                    )
                    circuit.append("MRX", [self.qX(i)])
                # identity gates on L data, moved to beginning of the round
                # circuit.append("DEPOLARIZE1", self.qL(i), self.p_before_round_data_depolarization)

            # X basis detector
            if not self.z_basis:
                if repeat:
                    circuit += detector_repeat_circuit
                else:
                    circuit += detector_circuit
            elif self.use_both and repeat:
                circuit += detector_repeat_circuit

            # tick
            circuit.append("TICK")

        for i in range(n // 2):  # ancilla initialization
            circuit.append("R", self.qX(i))
            circuit.append("R", self.qZ(i))
            circuit.append("X_ERROR", self.qX(i), self.p_after_reset_flip_probability)
            circuit.append("X_ERROR", self.qZ(i), self.p_after_reset_flip_probability)
        for q in data_qubits:
            circuit.append("R" if self.z_basis else "RX", q)
            circuit.append(
                "X_ERROR" if self.z_basis else "Z_ERROR",
                q,
                self.p_after_reset_flip_probability,
            )

        # begin round tick
        circuit.append("TICK")
        append_blocks(circuit, repeat=False)  # encoding round

        rep_circuit = Circuit()
        append_blocks(rep_circuit, repeat=True)
        circuit += (self.num_repeat - 1) * rep_circuit

        for q in data_qubits:
            # flip before collapsing data qubits
            # circuit.append("X_ERROR" if z_basis else "Z_ERROR", q, self.p_before_measure_flip_probability)
            circuit.append("M" if self.z_basis else "MX", q)

        pcm = self.H_Z if self.z_basis else self.H_X

        stab_detector_circuit_str = ""  # stabilizers
        for i, s in enumerate(pcm):
            det_str = "DETECTOR"
            for ind in np.nonzero(s)[0]:
                det_str += f" rec[{-n+ind}]"
            det_str += f" rec[{-n-n+i}]" if self.z_basis else f" rec[{-n-n//2+i}]"
            det_str += "\n"
            stab_detector_circuit_str += det_str
        stab_detector_circuit = Circuit(stab_detector_circuit_str)
        circuit += stab_detector_circuit

        log_detector_circuit_str = ""  # logical operators

        for i, (logical_x, logical_z) in enumerate(self.logical_operators):  # type: ignore
            logical = logical_z if self.z_basis else logical_x
            x_array, z_array = logical.to_numpy()
            assert not (
                x_array if self.z_basis else z_array
            ).any(), "X(Z) logical operator should not contain Z(X) errors"
            l = z_array if self.z_basis else x_array
            det_str = f"OBSERVABLE_INCLUDE({i})"
            for ind in np.nonzero(l)[0]:
                det_str += f" rec[{-n+ind}]"
            det_str += "\n"
            log_detector_circuit_str += det_str

        log_detector_circuit = Circuit(log_detector_circuit_str)
        circuit += log_detector_circuit

        return circuit


@code_cli("CircuitBBCode", "cbb")
def circuit_bb_code_cli(
    n: int,
    k: int,
    d: int,
    p: float = 0.0,
    p_after_clifford_depolarization: float | None = None,
    p_after_reset_flip_probability: float | None = None,
    p_before_measure_flip_probability: float | None = None,
    p_before_round_data_depolarization: float | None = None,
    num_repeat: int | None = None,
    z_basis: bool = True,
    use_both: bool = False,
    HZH: bool = False,
) -> CircuitBBCode:
    for params in bb_code_params:
        if params["nkd"] == (n, k, d):
            return CircuitBBCode(
                p=p,
                p_after_clifford_depolarization=p_after_clifford_depolarization,
                p_after_reset_flip_probability=p_after_reset_flip_probability,
                p_before_measure_flip_probability=p_before_measure_flip_probability,
                p_before_round_data_depolarization=p_before_round_data_depolarization,
                num_repeat=num_repeat if num_repeat is not None else d,
                z_basis=z_basis,
                use_both=use_both,
                HZH=HZH,
                **params,  # type: ignore
            )
    raise ValueError(f"no BBCode with n={n}, k={k}, d={d}")

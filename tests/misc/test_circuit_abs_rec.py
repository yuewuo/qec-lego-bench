from qec_lego_bench.misc.ref_circuit import *
import stim


def test_bb_code_construction():
    circuit_str = """\
R 0 1 2 3 4
TICK
CX 0 1 2 3
TICK
CX 2 1 4 3
TICK
MR 1 3
DETECTOR(1, 0) rec[-2]
DETECTOR(3, 0) rec[-1]
HERALDED_ERASE(0.01) 0
DETECTOR rec[-1]
M 0 2 4
DETECTOR(1, 1) rec[-2] rec[-3] rec[-6]
DETECTOR(3, 1) rec[-1] rec[-2] rec[-5]
OBSERVABLE_INCLUDE(0) rec[-1]\
"""
    circuit = stim.Circuit(circuit_str)
    print("######### original circuit #########")
    print(circuit)
    assert str(circuit) == circuit_str
    circuit_abs = RefCircuit(circuit)
    print("######### absolute indexed circuit #########")
    print(circuit_abs)
    assert (
        str(circuit_abs)
        == """\
R 0 1 2 3 4
TICK
CX 0 1 2 3
TICK
CX 2 1 4 3
TICK
MR 1 3
DETECTOR(1, 0) abs[0]
DETECTOR(3, 0) abs[1]
HERALDED_ERASE(0.01) 0
DETECTOR abs[2]
M 0 2 4
DETECTOR(1, 1) abs[4] abs[3] abs[0]
DETECTOR(3, 1) abs[5] abs[4] abs[1]
OBSERVABLE_INCLUDE(0) abs[5]\
"""
    )
    circuit_2 = circuit_abs.to_circuit()
    print("######### new circuit #########")
    print(circuit_2)
    assert isinstance(circuit_2, stim.Circuit)
    assert str(circuit_2) == circuit_str

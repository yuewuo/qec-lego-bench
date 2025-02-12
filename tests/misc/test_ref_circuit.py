from qec_lego_bench.misc.ref_circuit import *
import stim


def test_ref_circuit_simple():
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


def test_ref_circuit_heralded_erase_example():
    circuit_str_with_comment = """\
HERALDED_ERASE(0.01) 0
# Declare a flag detector based on the erasure
DETECTOR rec[-1]

# Erase qubit 2 with 2% probability
# Separately, erase qubit 3 with 2% probability
HERALDED_ERASE(0.02) 2 3

# Do an XXXX measurement
MPP X2*X3*X5*X7
# Apply partially-heralded noise to the two qubits
HERALDED_ERASE(0.01) 2 3 5 7
DEPOLARIZE1(0.0001) 2 3 5 7
# Repeat the XXXX measurement
MPP X2*X3*X5*X7
# Declare a detector comparing the two XXXX measurements
DETECTOR rec[-1] rec[-6]
# Declare flag detectors based on the erasures
DETECTOR rec[-2]
DETECTOR rec[-3]
DETECTOR rec[-4]
DETECTOR rec[-5]\
"""
    circuit_str = """\
HERALDED_ERASE(0.01) 0
DETECTOR rec[-1]
HERALDED_ERASE(0.02) 2 3
MPP X2*X3*X5*X7
HERALDED_ERASE(0.01) 2 3 5 7
DEPOLARIZE1(0.0001) 2 3 5 7
MPP X2*X3*X5*X7
DETECTOR rec[-1] rec[-6]
DETECTOR rec[-2]
DETECTOR rec[-3]
DETECTOR rec[-4]
DETECTOR rec[-5]\
"""
    circuit = stim.Circuit(circuit_str_with_comment)
    print("######### original circuit #########")
    print(circuit)
    assert str(circuit) == circuit_str
    circuit_abs = RefCircuit(circuit)
    print("######### absolute indexed circuit #########")
    print(circuit_abs)
    assert (
        str(circuit_abs)
        == """\
HERALDED_ERASE(0.01) 0
DETECTOR abs[0]
HERALDED_ERASE(0.02) 2 3
MPP X2*X3*X5*X7
HERALDED_ERASE(0.01) 2 3 5 7
DEPOLARIZE1(0.0001) 2 3 5 7
MPP X2*X3*X5*X7
DETECTOR abs[8] abs[3]
DETECTOR abs[7]
DETECTOR abs[6]
DETECTOR abs[5]
DETECTOR abs[4]\
"""
    )
    circuit_2 = circuit_abs.to_circuit()
    print("######### new circuit #########")
    print(circuit_2)
    assert isinstance(circuit_2, stim.Circuit)
    assert str(circuit_2) == circuit_str

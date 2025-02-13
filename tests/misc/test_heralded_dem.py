from qec_lego_bench.misc.heralded_dem import *
import stim


def test_heralded_dem_simple():
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
DEPOLARIZE1(0.02) 2
HERALDED_ERASE(0.01) 0
DETECTOR rec[-1]
M 0 2 4
DETECTOR(1, 1) rec[-2] rec[-3] rec[-6]
DETECTOR(3, 1) rec[-1] rec[-2] rec[-5]
OBSERVABLE_INCLUDE(0) rec[-1]\
"""
    circuit = stim.Circuit(circuit_str)
    dem = circuit.detector_error_model(approximate_disjoint_errors=True)
    print(dem)
    dem_str = """\
error(0.005) D2
error(0.005) D2 D3
error(0.01333333333333333) D3 D4
detector(1, 0) D0
detector(3, 0) D1
detector(1, 1) D3
detector(3, 1) D4
logical_observable L0\
"""
    assert str(dem) == dem_str
    # the regular dem does not contain
    heralded_dem = HeraldedDetectorErrorModel.of(circuit)
    skeleton_dem = heralded_dem.skeleton_dem.dem()
    print("######### skeleton dem #########")
    print(skeleton_dem)
    assert skeleton_dem.approx_equals(
        stim.DetectorErrorModel(
            """\
error(6.661338147750937e-16) D3
error(0.01333333333333333) D3 D4
detector(1, 0) D0
detector(3, 0) D1
detector(1, 1) D3
detector(3, 1) D4
logical_observable L0\
"""
        ),
        atol=DEM_MIN_PROBABILITY,
    )
    # that skeleton edge must exist
    assert not skeleton_dem.approx_equals(
        stim.DetectorErrorModel(
            """\
detector(1, 0) D0
detector(3, 0) D1
detector(1, 1) D3
detector(3, 1) D4
logical_observable L0\
"""
        ),
        atol=DEM_MIN_PROBABILITY,
    )

    print("######### heralded DEM #########")
    print(heralded_dem)
    assert (
        str(heralded_dem)
        == """\
HeraldedDetectorErrorModel:
    skeleton hypergraph:
        D3: 6.661338147750937e-16
        D3, D4: 0.013333333333333326
    heralded hypergraph on D2:
        D3: 0.5\
"""
    )


def test_heralded_dem_heralded_erase_example():
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
    heralded_dem = HeraldedDetectorErrorModel.of(circuit)
    print("######### skeleton circuit #########")
    print(heralded_dem.skeleton_circuit)
    assert (
        str(heralded_dem.skeleton_circuit)
        == """\
DEPOLARIZE1(1e-15) 0
DEPOLARIZE1(1e-15) 2 3
MPP X2*X3*X5*X7
DEPOLARIZE1(1e-15) 2 3 5 7
DEPOLARIZE1(0.0001) 2 3 5 7
MPP X2*X3*X5*X7
DETECTOR abs[1] abs[0]\
"""
    )
    print("######### heralded DEM #########")
    print(heralded_dem)
    assert (
        str(heralded_dem)
        == """\
HeraldedDetectorErrorModel:
    skeleton hypergraph:
        D1: 0.00026661333807661436
    heralded hypergraph on D2:
        D1: 0.5
    heralded hypergraph on D3:
        D1: 0.5
    heralded hypergraph on D4:
        D1: 0.5
    heralded hypergraph on D5:
        D1: 0.5\
"""
    )


def test_heralded_dem_heralded_pauli_channel_1_example():
    circuit_str_with_comment = """\
# With 10% probability perform a phase flip of qubit 0.
HERALDED_PAULI_CHANNEL_1(0, 0, 0, 0.1) 0
DETECTOR rec[-1]  # Include the herald in detectors available to the decoder

# With 20% probability perform a heralded dephasing of qubit 0.
HERALDED_PAULI_CHANNEL_1(0.1, 0, 0, 0.1) 0
DETECTOR rec[-1]

# Subject a Bell Pair to heralded noise.
MXX 0 1
MZZ 0 1
HERALDED_PAULI_CHANNEL_1(0.01, 0.02, 0.03, 0.04) 0 1
MXX 0 1
MZZ 0 1
DETECTOR rec[-1] rec[-5]  # Did ZZ stabilizer change?
DETECTOR rec[-2] rec[-6]  # Did XX stabilizer change?
DETECTOR rec[-3]    # Did the herald on qubit 1 fire?
DETECTOR rec[-4]    # Did the herald on qubit 0 fire?\
"""
    circuit_str = """\
HERALDED_PAULI_CHANNEL_1(0, 0, 0, 0.1) 0
DETECTOR rec[-1]
HERALDED_PAULI_CHANNEL_1(0.1, 0, 0, 0.1) 0
DETECTOR rec[-1]
MXX 0 1
MZZ 0 1
HERALDED_PAULI_CHANNEL_1(0.01, 0.02, 0.03, 0.04) 0 1
MXX 0 1
MZZ 0 1
DETECTOR rec[-1] rec[-5]
DETECTOR rec[-2] rec[-6]
DETECTOR rec[-3]
DETECTOR rec[-4]\
"""
    circuit = stim.Circuit(circuit_str_with_comment)
    print("######### original circuit #########")
    print(circuit)
    assert str(circuit) == circuit_str
    heralded_dem = HeraldedDetectorErrorModel.of(circuit)
    print("######### skeleton circuit #########")
    print(heralded_dem.skeleton_circuit)
    assert (
        str(heralded_dem.skeleton_circuit)
        == """\
PAULI_CHANNEL_1(0, 0, 1e-15) 0
PAULI_CHANNEL_1(0, 0, 1e-15) 0
MXX 0 1
MZZ 0 1
PAULI_CHANNEL_1(1e-15, 1e-15, 1e-15) 0 1
MXX 0 1
MZZ 0 1
DETECTOR abs[3] abs[1]
DETECTOR abs[2] abs[0]\
"""
    )
    print("######### heralded DEM #########")
    print(heralded_dem)
    assert (
        str(heralded_dem)
        == """\
HeraldedDetectorErrorModel:
    skeleton hypergraph:
        D2: 1.9984014443252798e-15
        D2, D3: 1.9984014443252798e-15
        D3: 1.9984014443252798e-15
    heralded hypergraph on D4:
        D2: 0.22222222222222224
        D2, D3: 0.3333333333333333
        D3: 0.4444444444444445
    heralded hypergraph on D5:
        D2: 0.22222222222222224
        D2, D3: 0.3333333333333333
        D3: 0.4444444444444445\
"""
    )


def test_heralded_dem_add_detectors():
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
HERALDED_ERASE(0.01) 0 2 1
M 0 2 4\
"""
    circuit = stim.Circuit(circuit_str)
    # add heralded detectors
    circuit_with_herald_detected = add_herald_detectors(circuit)
    print(circuit_with_herald_detected)
    assert (
        str(circuit_with_herald_detected)
        == """\
R 0 1 2 3 4
TICK
CX 0 1 2 3
TICK
CX 2 1 4 3
TICK
MR 1 3
DETECTOR(1, 0) rec[-2]
DETECTOR(3, 0) rec[-1]
HERALDED_ERASE(0.01) 0 2 1
DETECTOR rec[-3]
DETECTOR rec[-2]
DETECTOR rec[-1]
M 0 2 4\
"""
    )
    heralded_dem = HeraldedDetectorErrorModel.of(circuit)

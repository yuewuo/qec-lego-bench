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
detector(1, 0) D0
detector(3, 0) D1
detector(1, 1) D3
detector(3, 1) D4
logical_observable L0\
"""
    assert str(dem) == dem_str
    # the regular dem does not contain
    heralded_dem = HeraldedDetectorErrorModel(circuit)
    print(heralded_dem)

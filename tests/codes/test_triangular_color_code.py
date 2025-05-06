from qec_lego_bench.codes.stabilizer_codes.css_codes.triangular_color_code import (
    TriangularColorCode,
)


def test_triangular_color_code_coordinates():
    code = TriangularColorCode(d=7)
    assert code._range_for_row(0) == range(0, 13)
    assert code._range_for_row(1) == range(1, 13)
    assert code._range_for_row(2) == range(1, 12)
    assert code._range_for_row(3) == range(2, 11)
    assert code._range_for_row(4) == range(3, 11)
    assert code._range_for_row(5) == range(3, 10)

    assert code._is_any_qubit(0, 0)
    assert not code._is_any_qubit(1, 0)
    assert code._is_any_qubit(0, 12)
    assert not code._is_any_qubit(0, 13)
    assert code._is_any_qubit(1, 12)
    assert not code._is_any_qubit(1, 13)
    assert code._is_any_qubit(9, 6)
    assert not code._is_any_qubit(9, 7)
    assert not code._is_any_qubit(9, 5)

    assert code._is_data_qubit(0, 0)
    assert code._is_z_stabilizer(0, 1)
    assert code._is_x_stabilizer(0, 2)
    assert code._is_data_qubit(0, 3)
    assert code._is_data_qubit(1, 1)
    assert code._is_data_qubit(1, 2)
    assert code._is_z_stabilizer(1, 3)
    assert code._is_x_stabilizer(1, 4)

    assert len(code.qubit_coordinates) == code.n == 37
    assert (
        len(code.x_stabilizer_coordinates) == len(code.z_stabilizer_coordinates) == 18
    )

    code_d3 = TriangularColorCode(d=3)
    assert code_d3._range_for_row(0) == range(0, 5)
    assert code_d3._range_for_row(1) == range(1, 5)
    assert code_d3._range_for_row(2) == range(1, 4)
    assert code_d3._range_for_row(3) == range(2, 3)

    assert code_d3._is_any_qubit(0, 0)
    assert not code_d3._is_any_qubit(1, 0)
    assert code_d3._is_any_qubit(0, 4)
    assert not code_d3._is_any_qubit(0, 5)
    assert code_d3._is_any_qubit(1, 4)
    assert not code_d3._is_any_qubit(1, 5)
    assert code_d3._is_any_qubit(2, 3)
    assert not code_d3._is_any_qubit(2, 4)
    assert code_d3._is_any_qubit(3, 2)
    assert not code_d3._is_any_qubit(3, 1)
    assert not code_d3._is_any_qubit(3, 3)


# pytest tests/codes/test_triangular_color_code.py::test_triangular_color_code_circuit -s --no-cov
# import to https://algassert.com/crumble for circuit visualization
def test_triangular_color_code_circuit():
    code = TriangularColorCode(d=5)
    circuit = code.circuit
    print(circuit)

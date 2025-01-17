from qec_lego_bench.codes.stabilizer_codes.css_codes.bb_code import BBCode


def test_bb_code_construction():
    code = BBCode()


import stim

tableau = stim.Tableau.from_conjugated_generators(
    xs=[
        stim.PauliString("+YZ__"),
        stim.PauliString("-Y_XY"),
        stim.PauliString("+___Y"),
        stim.PauliString("+YZX_"),
    ],
    zs=[
        stim.PauliString("+XZYY"),
        stim.PauliString("-XYX_"),
        stim.PauliString("-ZXXZ"),
        stim.PauliString("+XXZ_"),
    ],
)
print(tableau)

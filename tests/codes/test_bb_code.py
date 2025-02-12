from qec_lego_bench.codes.stabilizer_codes.css_codes.bb_code import bb_code_cli


def test_bb_code_construction():
    code = bb_code_cli(n=72, k=12, d=6)
    print(code)

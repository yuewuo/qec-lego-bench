import arguably
import sinter
from qec_lego_bench.stats import Stats
import os


def read_01(filepath: str) -> list[tuple[int, ...]]:
    result = []
    with open(filepath) as f:
        for line in f.readlines():
            line = line.strip("\r\n ")
            if line.startswith("#") or line == "":
                continue
            value = tuple(int(e) for e in line.split(" "))
            result.append(value)
    return result


@arguably.command
def compare_01(file1: str, file2: str):
    assert os.path.exists(file1)
    assert os.path.exists(file2)
    data1 = read_01(file1)
    data2 = read_01(file2)
    assert len(data1) == len(data2)
    shots = len(data1)
    errors = 0
    for v1, v2 in zip(data1, data2):
        if v1 != v2:
            errors += 1
    stats = Stats(sinter.AnonTaskStats(shots=shots, errors=errors))
    print(stats)

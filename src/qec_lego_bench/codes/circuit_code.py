from stim import Circuit
from .code import Code
from qec_lego_bench.cli.codes import code_cli


@code_cli("CircuitCode", "file")
class CircuitCode(Code):
    """
    A code directly from a circuit in a file
    """

    skip_read_file: bool = False

    def __init__(self, filepath: str):
        if not self.skip_read_file:
            self._circuit = Circuit.from_file(filepath)
        super().__init__()

    @property
    def circuit(self) -> Circuit:
        return self._circuit

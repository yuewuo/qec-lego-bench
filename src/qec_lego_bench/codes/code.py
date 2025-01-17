from abc import ABC, abstractmethod
from stim import Circuit, DetectorErrorModel


class Code(ABC):
    @property
    @abstractmethod
    def circuit(self) -> Circuit: ...

    def init_dem(self):
        self._dem = self.circuit.detector_error_model()
        print(repr(self._dem))

    @property
    def dem(self) -> DetectorErrorModel:
        return self._dem

    def __init__(self):
        self.init_dem()

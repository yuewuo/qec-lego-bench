from abc import ABC, abstractmethod
from stim import Circuit, DetectorErrorModel


class Code(ABC):
    @property
    @abstractmethod
    def circuit(self) -> Circuit: ...

from abc import ABC, abstractmethod
from stim import Circuit


class Code(ABC):
    @property
    @abstractmethod
    def circuit(self) -> Circuit: ...

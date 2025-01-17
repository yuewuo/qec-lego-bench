from abc import ABC, abstractmethod
import stim


class Noise(ABC):
    @abstractmethod
    def apply(self, circuit: stim.Circuit) -> stim.Circuit: ...

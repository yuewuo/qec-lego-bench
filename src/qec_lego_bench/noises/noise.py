from abc import ABC, abstractmethod
import stim


class Noise(ABC):
    @abstractmethod
    def __call__(self, circuit: stim.Circuit) -> stim.Circuit: ...

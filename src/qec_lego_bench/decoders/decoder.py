from abc import ABC, abstractmethod
import stim


class Decoder(ABC):
    @staticmethod
    @abstractmethod
    def from_stim(circuit: stim.Circuit): ...

    @abstractmethod
    def decode(self, circuit: stim.Circuit) -> stim.Circuit: ...

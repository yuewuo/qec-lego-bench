from abc import ABC, classmethod, abstractmethod
import stim


class Decoder(ABC):
    @classmethod
    def from_stim(circuit: stim.Circuit): ...

    @abstractmethod
    def decode(self, circuit: stim.Circuit) -> stim.Circuit: ...

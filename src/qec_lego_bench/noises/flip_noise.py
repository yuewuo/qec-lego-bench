from .noise import Noise
from dataclasses import dataclass


@dataclass
class FlipNoise(Noise):
    basis: str  # "X", "Z" or "Y"

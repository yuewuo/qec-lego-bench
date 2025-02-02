import sinter
import numpy as np
from uncertainties import ufloat
import math


def precision_to_errors(precision: float) -> int:
    # precision * errors/shots ~= 2.58 * sqrt(errors)/shots
    return math.ceil((2.58 / precision) ** 2)


class Stats:

    def __init__(self, stats: sinter.TaskStats | sinter.AnonTaskStats):
        self.stats = stats

    @property
    def errors(self) -> int:
        return self.stats.errors

    @property
    def failed(self) -> int:
        return self.stats.errors

    @property
    def shots(self) -> int:
        return self.stats.shots

    @property
    def samples(self) -> int:
        return self.stats.shots - self.stats.discards

    @property
    def samples_including_discards(self) -> int:
        return self.stats.shots

    @property
    def discards(self) -> int:
        return self.stats.discards

    @property
    def duration(self) -> float:
        return float(self.stats.seconds)

    @property
    def speed(self) -> float:
        return self.samples / self.duration

    @property
    def average_duration(self) -> float:
        return self.duration / self.samples_including_discards

    @property
    def failure_rate_value(self) -> float:
        return self.failed / self.samples

    @property
    def failure_rate_uncertainty(self) -> float:
        failure_rate_value = self.failure_rate_value
        # confidence interval = 2.58 * sqrt(p * (1-p) / N) using 99% confidence interval
        return 2.58 * np.sqrt(
            failure_rate_value * (1.0 - failure_rate_value) / self.samples
        )

    @property
    def relative_uncertainty(self) -> float:
        return self.failure_rate_uncertainty / self.failure_rate_value

    @property
    def failure_rate(self):
        return ufloat(self.failure_rate_value, self.failure_rate_uncertainty)

    def __str__(self) -> str:
        if self.samples == 0:
            return "Stats{ 0/0 }"
        return f"Stats{{ pL = {self.str_pL()}{self.str_speed(', speed=')} }}"

    def str_pL(self) -> str:
        return f"{self.failed}/{self.samples}= {self.failure_rate:.1uS}"

    def str_speed(self, prefix: str = "") -> str:
        if self.duration != 0:
            return f"{prefix}{self.average_duration:.2e}s/S"
        return ""

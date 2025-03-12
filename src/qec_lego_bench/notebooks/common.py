from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from qec_lego_bench.hpc.monte_carlo import MonteCarloResult, LogicalErrorResult
from qec_lego_bench.hpc.monte_carlo import *


@dataclass_json(undefined="RAISE")  # avoid accidentally override other types
@dataclass
class MultiDecoderLogicalErrorRates(MonteCarloResult):
    results: dict[str, LogicalErrorResult] = field(default_factory=dict)

    def __add__(
        self, other: "MultiDecoderLogicalErrorRates"
    ) -> "MultiDecoderLogicalErrorRates":
        results = self.results.copy()
        for decoder, result in other.results.items():
            if decoder in results:
                results[decoder] += result
            else:
                results[decoder] = result
        return MultiDecoderLogicalErrorRates(results=results)

    @property
    def errors(self) -> int:
        # used by the submitter, return the smallest number of errors
        errors = None
        for result in self.results.values():
            if errors is None or result.errors < errors:
                errors = result.errors
        return errors or 0

    @property
    def discards(self) -> int:
        return 0

    @property
    def panics(self) -> int:
        return 0

    def stats_of(self, job: "MonteCarloJob") -> Stats:
        return Stats(
            stats=sinter.AnonTaskStats(
                shots=job.shots,
                errors=self.errors,
                seconds=job.duration,
            ),
        )

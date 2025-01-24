from ..monte_carlo import *


def precision_to_errors(precision: float) -> int:
    # precision * errors/shots ~= 2.58 * sqrt(errors)/shots
    return math.ceil((2.58 / precision) ** 2)


@dataclass
class PrecisionSubmitter:
    # the minimum precision before trying to achieve the target precision
    min_precision: float = 0.5
    # the target precision,
    target_precision: float = 0.03
    # maximum CPU time to spend on each data point (roughly)
    time_limit: float = 3600
    # minimum number of shots to submit
    min_shots: int = 100

    def __call__(
        self, jobs: Iterable[MonteCarloJob]
    ) -> list[tuple[MonteCarloJob, int]]:
        submit = []
        for job in jobs:
            if job.result is None:
                continue
            if job.duration >= self.time_limit:
                continue
            errors = job.result.errors  # type: ignore
            if errors < precision_to_errors(self.min_precision):
                continue
            target_errors = precision_to_errors(self.target_precision)
            target_shots = math.ceil(target_errors / errors * job.shots)
            if target_shots < job.expecting_shots:
                continue
            remaining_shots = target_shots - job.expecting_shots
            if (
                remaining_shots * job.duration_per_shot - job.duration
            ) > self.time_limit:
                remaining_shots = math.ceil(
                    (self.time_limit - job.duration) / job.duration_per_shot
                )
            if remaining_shots > 0:
                submit.append((job, max(remaining_shots, self.min_shots)))
        return submit

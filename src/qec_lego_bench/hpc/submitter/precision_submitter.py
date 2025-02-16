from ..monte_carlo import *
from qec_lego_bench.stats import precision_to_errors


@dataclass
class PrecisionSubmitter:
    # the minimum precision before trying to achieve the target precision
    min_precision: float | None = 0.5
    # the target precision,
    target_precision: float = 0.03
    # maximum CPU time to spend on each data point (roughly)
    time_limit: float | None = 3600
    # minimum number of shots to submit
    min_shots: int = 100

    # also check if the logical error rate is too high (pL > high_pL_threshold)
    high_pL_threshold: float = 0.1
    # if so, we don't have to reach that precision because such points are meaningless anyway
    high_pL_precision: float = 0.2

    def __call__(
        self, jobs: Iterable[MonteCarloJob]
    ) -> list[tuple[MonteCarloJob, int]]:
        submit = []
        print("Submitting jobs precision called")
        for job in jobs:
            if job.result is None:
                continue
            if self.time_limit is not None and job.duration >= self.time_limit:
                continue
            errors = job.result.errors  # type: ignore
            if self.min_precision is not None and errors < precision_to_errors(
                self.min_precision
            ):
                continue
            target_precision = self.target_precision
            if errors / job.shots > self.high_pL_threshold:
                target_precision = self.high_pL_precision
            target_errors = precision_to_errors(target_precision)
            if errors < 10:
                target_shots = job.shots * 2  # double the shots
            else:
                target_shots = math.ceil(target_errors / errors * job.shots)
            if target_shots < job.expecting_shots:
                continue
            remaining_shots = target_shots - job.expecting_shots
            if (
                self.time_limit is not None
                and (remaining_shots * job.duration_per_shot - job.duration)
                > self.time_limit
            ):
                remaining_shots = math.ceil(
                    (self.time_limit - job.duration) / job.duration_per_shot
                )
            if remaining_shots > 0:
                submit.append((job, max(remaining_shots, self.min_shots)))
        return submit

from ..monte_carlo import *


@dataclass
class AdaptiveMinShotsSubmitter:
    min_shots: int = 1000
    max_shots: int = 1000000
    # accumulate at most these number of errors before it terminates
    max_errors: int = 100
    # maximum CPU time to spend on each data point (roughly)
    time_limit: float | None = 3600

    def __call__(
        self, executor: MonteCarloJobExecutor
    ) -> list[tuple[MonteCarloJob, int]]:
        submit = []
        for job in executor:
            if job.result is None:
                if job.expecting_shots < self.min_shots:
                    submit.append((job, self.min_shots - job.expecting_shots))
                    continue
            if self.time_limit is not None and job.duration >= self.time_limit:
                # don't spend time on this anymore
                continue
            if job.result is None:
                if job.expecting_shots < self.max_shots:
                    new_expecting = min(job.finished_shots * 2, self.max_shots)
                    if new_expecting > job.expecting_shots:
                        submit.append((job, new_expecting - job.expecting_shots))
                        continue
                continue
            errors = job.result.errors  # type: ignore
            if errors >= self.max_errors:
                continue
            if job.expecting_shots < self.max_shots:
                new_expecting = min(job.finished_shots * 2, self.max_shots)
                if new_expecting > job.expecting_shots:
                    submit.append((job, new_expecting - job.expecting_shots))
                    continue

        # otherwise use the same shots
        return submit

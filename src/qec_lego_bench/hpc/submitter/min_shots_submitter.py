from ..monte_carlo import *


@dataclass
class MinShotsSubmitter:
    shots: int = 1000

    def __call__(
        self, jobs: Iterable[MonteCarloJob]
    ) -> list[tuple[MonteCarloJob, int]]:
        return [
            (job, self.shots - job.expecting_shots)
            for job in jobs
            if job.expecting_shots < self.shots
        ]

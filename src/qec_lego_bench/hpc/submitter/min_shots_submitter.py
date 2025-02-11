from ..monte_carlo import *


@dataclass
class MinShotsSubmitter:
    shots: int = 1000
    shots_vec: Optional[list[int]] = None

    def __call__(
        self, jobs: Iterable[MonteCarloJob]
    ) -> list[tuple[MonteCarloJob, int]]:
        if self.shots_vec is not None:
            # the shots vector is provided, use it
            return [
                (
                    job,
                    self.shots_vec[job_index % len(self.shots_vec)]
                    - job.expecting_shots,
                )
                for job_index, job in enumerate(jobs)
                if job.expecting_shots < self.shots_vec[job_index % len(self.shots_vec)]
            ]

        # otherwise use the same shots
        return [
            (job, self.shots - job.expecting_shots)
            for job in jobs
            if job.expecting_shots < self.shots
        ]

from ..monte_carlo import *


@dataclass
class SmallLogicalErrorRateSubmitter:
    """
    check the previous two jobs and extrapolate
    """

    physical_error_rate_key: str = "p"

    def __call__(
        self, jobs: Iterable[MonteCarloJob]
    ) -> list[tuple[MonteCarloJob, int]]:
        submit = []
        # first gather the jobs belonging to the same configuration
        ...
        return submit

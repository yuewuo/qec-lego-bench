from ..monte_carlo import *


@dataclass
class SubmitterBarrier:
    is_previous_all_finished: bool = False

    def __call__(
        self,
        executor: MonteCarloJobExecutor,
        previous_submit: list[tuple[MonteCarloJob, int]],
    ) -> bool:
        if len(previous_submit) == 0 and executor.no_pending():
            self.is_previous_all_finished = True
        return self.is_previous_all_finished

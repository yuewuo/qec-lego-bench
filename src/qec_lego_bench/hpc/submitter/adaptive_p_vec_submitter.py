from ..monte_carlo import *
from dotmap import DotMap
from qec_lego_bench.stats import precision_to_errors


@dataclass
class AdaptivePVecSubmitter:
    config_vec: list[DotMap]
    ap_vec: "AdaptivePVec"

    # range of p variants to try in parallel (to the lower side), per config;
    # to the upper side, let's just try the values one by one cause they are less important and much fewer values
    parallel_p_range: float = 10.0

    max_pL: float = 0.3  # we don't care logical error rate beyond this value
    min_pL: float = 1e-5  # we don't evaluate logical error rate below this value
    # all the configs that has pL >= min_pL are subject to this target precision
    target_precision: float = 0.1
    # only when the precision of a config reaches this precision, do we start to consider it as a valid data point
    min_precision: float = 0.3
    # maximum CPU time to spend on each data point (roughly)
    time_limit: float = 3600
    # minimum number of shots to submit
    min_shots: int = 1000

    @property
    def max_shots_when_untrusted(self) -> int:
        return round(3 / self.min_pL)

    @property
    def parallel_p_count(self) -> int:
        return max(
            1, math.ceil(math.log10(self.parallel_p_range) * self.ap_vec.per10_p_count)
        )

    def __call__(
        self, executor: MonteCarloJobExecutor
    ) -> list[tuple[MonteCarloJob, int]]:
        submit = []
        for config in self.config_vec:
            current_jobs = self.ap_vec.jobs(executor, config)
            # check if each value reaches the minimum precision to be trusted
            trusted_jobs = []
            for job in current_jobs:
                if job.result is None:
                    if job.expecting_shots < self.min_shots:
                        submit.append((job, self.min_shots - job.expecting_shots))
                    continue
                errors = job.result.errors  # type: ignore
                if errors >= precision_to_errors(self.min_precision):
                    trusted_jobs.append(job)
                    # handle it later
                    continue
                if job.duration >= self.time_limit:
                    # don't spend time on this anymore
                    continue
                # should I give it more samples to try?
                if errors < 3:
                    # if it's too small, then we should give it more samples until 3/self.min_pL;
                    # but doing so gradually, because we don't want to over submit too much samples
                    if job.expecting_shots < self.min_shots:
                        submit.append((job, self.min_shots - job.expecting_shots))
                    elif job.finished_shots >= job.expecting_shots / 2:
                        # already finished half of the shots yet still haven't found an error, make it larger!
                        total_shots = min(
                            job.finished_shots * 3, self.max_shots_when_untrusted
                        )
                        if total_shots > job.expecting_shots:
                            submit.append((job, total_shots - job.expecting_shots))
                    # else, just wait for it to do some work
                else:
                    # we can safely use the current data point to submit more shots
                    total_shots = round(
                        precision_to_errors(self.min_precision)
                        / errors
                        * job.finished_shots
                    )
                    total_shots = min(total_shots, self.max_shots_when_untrusted)
                    if total_shots > job.expecting_shots:
                        submit.append((job, total_shots - job.expecting_shots))
            # now let's handle the trusted data points. We can safely use them to create more p values
            for job in trusted_jobs:
                p: float = job["p"]
                job_config: DotMap = job["config"]
                i = self.ap_vec.i(p)
                # first of all, let's make sure we submit more jobs to the lower side and the upper side
                for parallel_i in range(i - self.parallel_p_count, i + 2):  # also i+1
                    parallel_p = self.ap_vec.p(parallel_i)
                    if parallel_p > self.ap_vec.p_upper:
                        continue
                    parallel_job = executor.get_job(config=job_config, p=parallel_p)
                    if parallel_job is None:
                        # create this job according to the `parallel_p_range` parameter
                        parallel_job = MonteCarloJob(config=job_config, p=parallel_p)
                        executor.add_job(parallel_job)
                # then, let's try to make the trusted job to reach the target precision, if time permits
                if job.duration >= self.time_limit:
                    # don't spend time on this anymore
                    continue
                errors = job.result.errors  # type: ignore
                total_shots = round(
                    precision_to_errors(self.target_precision)
                    / errors
                    * job.finished_shots
                )
                if total_shots > job.expecting_shots:
                    submit.append((job, total_shots - job.expecting_shots))
        return submit


@dataclass
class AdaptivePVec:
    p_center: float  # center p to start searching
    per10_p_count: int  # how many p to take per x10 interval
    p_upper: float = (
        0.4  # maximum value of physical error rate; usually 40% but could be lower for some noise mode
    )

    # one should always use this function to calculate p from index, otherwise it might causes numerical error
    def p(self, i: int) -> float:
        return self.p_center * 10 ** (i / self.per10_p_count)

    # revert back to the index
    def i(self, p: float) -> int:
        return round(self.per10_p_count * math.log10(p / self.p_center))

    # find the index vector for a given config in an executor
    def i_vec(
        self, executor: MonteCarloJobExecutor, config: DotMap, searching_for: int = 20
    ) -> list[int]:
        assert (
            executor.get_job(p=self.p_center, config=config) is not None
        ), "p_center should exist in the executor"
        assert searching_for > 0
        i_vec = [0]
        # first find the lower side
        lower_i = -1
        while True:
            found = False
            for i in range(lower_i, lower_i - searching_for, -1):
                p = self.p(i)
                if executor.get_job(p=p, config=config) is not None:
                    i_vec.append(i)
                    lower_i = i - 1
                    found = True
                    break
            if not found:
                break
        # then search the upper side
        upper_i = 1
        while True:
            found = False
            for i in range(upper_i, upper_i + searching_for):
                p = self.p(i)
                if p > self.p_upper:
                    break
                if executor.get_job(p=p, config=config) is not None:
                    i_vec.append(i)
                    upper_i = i + 1
                    found = True
                    break
            if not found:
                break
        i_vec.sort()
        return i_vec

    # find the p vector for a given config in an executor
    def p_vec(
        self, executor: MonteCarloJobExecutor, config: DotMap, searching_for: int = 20
    ) -> list[float]:
        i_vec = self.i_vec(executor, config, searching_for)
        return [self.p(i) for i in i_vec]

    def jobs(
        self, executor: MonteCarloJobExecutor, config: DotMap, searching_for: int = 20
    ) -> list[MonteCarloJob]:
        return [
            executor.get_job_assert(p=p, config=config)
            for p in self.p_vec(executor, config, searching_for)
        ]

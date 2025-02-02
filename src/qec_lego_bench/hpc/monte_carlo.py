from typing import (
    Any,
    Protocol,
    Callable,
    TypeVar,
    Type,
    Iterator,
    Optional,
    Tuple,
    Concatenate,
    cast,
    Sequence,
    Iterable,
    ParamSpec,
)
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from distributed import (
    Future,
    Client,
    wait,
    TimeoutError as DaskTimeoutError,
    as_completed,
)
from concurrent.futures._base import DoneAndNotDoneFutures, FIRST_COMPLETED
from concurrent.futures import Future as ConcurrentFuture
import time
import sys
import math
import sinter
from qec_lego_bench.stats import Stats
import json
import portalocker
import os
from .job_store import JobParameters
from .panic_store import PanicStore, JobPanic
import traceback


def hex_hash(value: Any) -> str:
    sign_mask = (1 << sys.hash_info.width) - 1
    return f"{hash(value) & sign_mask:0{sys.hash_info.width//4}X}"


class MonteCarloResult(Protocol):
    def __add__(self: "Result", other: "Result") -> "Result": ...

    # the following two methods are automatically generated by the dataclass_json decorator
    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls: Type["Result"], value: dict) -> "Result": ...


Result = TypeVar("Result", bound=MonteCarloResult)


@dataclass_json
@dataclass
class LogicalErrorResult(MonteCarloResult):
    errors: int = 0
    discards: int = 0

    def __add__(self, other: "LogicalErrorResult") -> "LogicalErrorResult":
        return LogicalErrorResult(self.errors + other.errors, self.discards + other.discards)  # type: ignore

    def stats_of(self, job: "MonteCarloJob") -> Stats:
        return Stats(
            sinter.AnonTaskStats(
                shots=job.shots,
                errors=self.errors,
                discards=self.discards,
                seconds=job.duration,
            )
        )


"""
A function to run the Monte Carlo result, given the number of shots and other parameters provided by the user
"""
P = ParamSpec("P")
MonteCarloFunc = Callable[Concatenate[int, P], Tuple[int, MonteCarloResult]]

"""
A function to decide which is the next job to run and how many shots to run
"""
MonteCarloJobSubmitter = Callable[
    ["MonteCarloJobExecutor"], Iterable[Tuple["MonteCarloJob", int]]
]


def empty_submitter(
    executor: "MonteCarloJobExecutor",
) -> Iterable[Tuple["MonteCarloJob", int]]:
    return []


class MonteCarloJob:

    def __init__(self, *args, **kwargs) -> None:
        self._params = JobParameters(args, kwargs)
        self.finished_shots: int = 0
        self.pending_shots: int = 0
        self.duration: float = 0  # overall time of the finished shots
        self.result: Optional[MonteCarloResult] = None
        self.min_time: Optional[float] = None  # an estimation of the init time

    def __repr__(self):
        args = [str(arg) for arg in self.args]
        for key in self.kwargs.keys():
            args.append(f"{key}={self.kwargs[key]}")
        return f"Job({', '.join(args)})"

    @property
    def args(self) -> tuple:
        return self._params.args

    @property
    def kwargs(self) -> dict:
        return self._params.kwargs

    def __getitem__(self, key: str) -> Any:
        return self.kwargs[key]

    @property
    def expecting_shots(self) -> int:
        return self.pending_shots + self.finished_shots

    @property
    def shots(self) -> int:
        return self.finished_shots

    @property
    def duration_per_shot(self) -> float:
        return self.duration / self.finished_shots

    @property
    def hash(self) -> str:
        return self._params.hash

    @property
    def parameters(self) -> JobParameters:
        return self._params


@dataclass
class MonteCarloExecutorConfig:
    # at least run 100 shots before sufficient estimation time is reached
    min_shots_before_estimation: int = 100
    # run at least 30s for single thread before it can spawn multiple
    min_multi_thread_duration: float = 30
    # let each job run for about 3 minutes to reduce scheduling overhead
    target_job_time: float = 180
    # the max time for each job to run including the initialization time
    max_job_time: float = 3600
    # a loose upper bound of how many submitted jobs there could be, because of memory leak
    # in dask library: https://github.com/dask/distributed/pull/6342;
    max_submitted_job: int = 1000
    # iteratively call the submitter function until no job is submitted
    iterative_submitter: bool = True

    # return the split of the shots and how many threads
    def warmed_up_split(self, job: MonteCarloJob, shots: int) -> Tuple[int, int]:
        if job.min_time is None:
            return 1, 1  # submit one shot as an estimation of the initialization time
        if job.finished_shots < self.min_shots_before_estimation:
            return self.min_shots_before_estimation, 1
        per_shot_time = (job.duration - job.min_time) / job.finished_shots
        if job.duration - job.min_time < self.min_multi_thread_duration:
            target_shots = int(self.min_multi_thread_duration / per_shot_time)
            target_shots = min(shots, target_shots)
            return target_shots, 1
        # we have gathered sufficient data to estimate the runtime
        if job.min_time > self.max_job_time / 3:
            print(
                f"[warning] job init time {job.min_time:.1f}s exceeds 1/3 of the maximum job time of {self.max_job_time:.1f}s"
            )
        target_job_time = min(self.target_job_time, self.max_job_time)
        target_job_time = max(target_job_time, job.min_time * 3)
        if shots * per_shot_time < target_job_time:
            return shots, 1
        threads = math.ceil(shots * per_shot_time / (target_job_time - job.min_time))
        shots_per_thread = math.ceil(shots / threads)
        return shots_per_thread, threads


@dataclass
class MonitoredResult:
    result: MonteCarloResult | None
    shots: int = 0
    actual_shots: int = 0
    duration: float = 0
    panic_info: Optional[str] = None


def monitored_job(
    func: MonteCarloFunc, shots: int, job_id: int, args: tuple, kwargs: dict
) -> MonitoredResult:
    start = time.thread_time()
    actual_shots, result, panic_info = 0, None, None
    try:
        actual_shots, result = func(shots, *args, **kwargs)
    except Exception as e:
        panic_info = traceback.format_exc()
    duration = time.thread_time() - start
    return MonitoredResult(result, shots, actual_shots, duration, panic_info=panic_info)


class MonteCarloJobExecutor:
    def __init__(
        self,
        func: MonteCarloFunc,
        jobs: Sequence[MonteCarloJob],
        config: Optional[MonteCarloExecutorConfig] = None,
        filename: Optional[str] = None,
        panic_filename: Optional[
            str
        ] = None,  # hjson file to store the panic information
        # used when reading from file
        result_type: Type[MonteCarloResult] = LogicalErrorResult,
    ) -> None:
        assert callable(func)
        config = config or MonteCarloExecutorConfig()
        self.config = config
        self.func = func
        self.jobs: dict[str, MonteCarloJob] = {job.hash: job for job in jobs}
        self.pending_futures: list[Future] = []
        self.future_info: dict[Future, MonteCarloJob] = {}
        # the remaining shots due to insufficient number of samples for estimation runtime
        self.pending_submit: dict[MonteCarloJob, tuple[int, Future]] = {}
        self.filename = filename
        if panic_filename is None:
            if filename is not None:
                panic_filename = filename + ".panic.hjson"
            else:
                panic_filename = "panic.hjson"
        self.panics = PanicStore(panic_filename)
        self.result_type = result_type
        self.num_jobs = 0  # used to uniquely set job ID to avoid caching
        if filename is not None:
            self.load_from_file(filename)  # load from file on initialization

    def __iter__(self) -> Iterator[MonteCarloJob]:
        for job in self.jobs.values():
            yield job

    def add_job(
        self,
        job: MonteCarloJob,
        load_from_file: bool = True,
        skip_if_exists: bool = False,
    ) -> None:
        if skip_if_exists and job.hash in self.jobs:
            return
        assert job.hash not in self.jobs, "Job already exists"
        self.jobs[job.hash] = job
        if load_from_file and self.filename is not None:
            self.load_from_file(self.filename, job)

    def get_job(self, *args, **kwargs) -> Optional[MonteCarloJob]:
        hash_value = JobParameters(args, kwargs).hash
        if hash_value not in self.jobs:
            return None
        return self.jobs[hash_value]

    def get_job_assert(self, *args, **kwargs) -> MonteCarloJob:
        job = self.get_job(*args, **kwargs)
        assert job is not None, f"Job not found: {args}, {kwargs}"
        return job

    def execute(
        self,
        client: Optional[Client] = None,  # prefer to use `client_connector` instead
        submitter: MonteCarloJobSubmitter = empty_submitter,
        timeout: float = sys.float_info.max,
        loop_callback: Optional[Callable[["MonteCarloJobExecutor"], None]] = None,
        force_finished: bool = False,
        client_connector: Optional[Callable[[], Client]] = None,
        shutdown_cluster: bool = False,
    ) -> None:
        if client is not None:
            assert isinstance(client, Client)
        if loop_callback is not None:
            loop_callback(self)
        start = time.time()
        try:
            while True:
                if client is not None:
                    remaining_time = timeout - (time.time() - start)
                    if remaining_time <= 0:
                        raise TimeoutError()
                    try:
                        futures: DoneAndNotDoneFutures = wait(
                            self.pending_futures,
                            return_when=FIRST_COMPLETED,
                            timeout=timeout - (time.time() - start),
                        )
                    except DaskTimeoutError as e:
                        raise TimeoutError()
                    assert len(futures.done) + len(futures.not_done) == len(
                        self.pending_futures
                    ), "API error"
                    for done, job_result in as_completed(
                        futures.done, with_results=True
                    ):
                        job_result = cast(MonitoredResult, job_result)
                        assert isinstance(done, Future)
                        job = self.future_info[done]
                        if job_result.panic_info is not None:
                            # job panics, record it
                            self.panics.add_panic(
                                JobPanic(
                                    parameters=job.parameters,
                                    latest=json.dumps(
                                        dict(shots=job.shots, duration=job.duration)
                                    ),
                                ).add_panic(job_result.panic_info)
                            )
                        else:
                            result = job_result.result
                            assert result is not None
                            if job.result is None:
                                job.result = result
                            else:
                                job.result += result
                            job.duration += job_result.duration
                            job.finished_shots += job_result.actual_shots
                            job.pending_shots -= job_result.shots
                            if job.min_time is None:
                                job.min_time = job_result.duration
                            else:
                                job.min_time = min(job.min_time, job_result.duration)
                        del self.future_info[done]
                        client.cancel(done)
                    self.pending_futures = list(futures.not_done)  # type: ignore
                # get the next job to run
                while True:
                    # make the development of the submitter easier by iteratively call them
                    last_job_count = len(self.jobs)
                    submit = list(submitter(self))
                    if len(submit) == 0 and last_job_count == len(self.jobs):
                        break
                    # run those jobs
                    for job, shots in submit:
                        assert shots >= 0
                        if shots == 0:
                            continue
                        # submit jobs such that it runs for this number of shots
                        job.pending_shots += shots
                        if job in self.pending_submit:
                            remaining, blocking_future = self.pending_submit[job]
                            self.pending_submit[job] = (
                                remaining + shots,
                                blocking_future,
                            )
                        else:
                            # add the job to the pending submit and mock a done job such that it will be submitted later
                            mock_future: ConcurrentFuture = ConcurrentFuture()
                            mock_future.set_result(0)
                            self.pending_submit[job] = shots, cast(Future, mock_future)
                    if not self.config.iterative_submitter:  # backward compatible
                        break
                # fair submission
                while (
                    not force_finished
                    and len(self.future_info) < self.config.max_submitted_job
                ):
                    has_any_submission = False
                    for job in list(self.pending_submit.keys()):
                        if job.parameters in self.panics:
                            continue  # do not submit any job that has panicked before
                        shots, done_future = self.pending_submit[job]
                        if not done_future.done():
                            continue  # keep waiting
                        del self.pending_submit[job]
                        shots_per_thread, threads = self.config.warmed_up_split(
                            job, shots
                        )
                        has_any_submission = True
                        if client is None:
                            assert client_connector is not None
                            print("winding up a new client")
                            client = client_connector()
                        future = client.submit(
                            monitored_job,
                            self.func,
                            shots_per_thread,
                            self.num_jobs,
                            job.args,
                            job.kwargs,
                        )
                        self.num_jobs += 1
                        self.pending_futures.append(future)
                        self.future_info[future] = job
                        actual_shots = shots_per_thread
                        if actual_shots < shots:
                            self.pending_submit[job] = shots - actual_shots, (
                                future if threads == 1 else done_future
                            )
                        else:
                            # adjust actual pending shots
                            job.pending_shots += actual_shots - shots
                    if not has_any_submission:
                        break  # search next round
                # save to file
                if client is not None and self.filename is not None:
                    self.update_file(self.filename)
                # call user callback such that they can do some plotting of the intermediate results
                if loop_callback is not None:
                    loop_callback(self)
                if not self._loop_again():
                    break
                if len(self.pending_futures) == 0 and len(self.pending_submit) == 0:
                    break
                if client is None:
                    break
        finally:
            # cancel all pending futures
            for future in self.pending_futures:
                try:
                    future.cancel()
                except Exception as e:
                    print("cancel failed", e)
            self.pending_futures = []
            self.future_info.clear()
            self.pending_submit.clear()
            for job in self:
                job.pending_shots = 0
            if shutdown_cluster and client is not None:
                print(
                    "shutting down the cluster; if this is not desired, set `shutdown_cluster` to `False`"
                )
                client.shutdown()

    def _loop_again(self) -> bool:
        if len(self.pending_futures) > 0:
            return True
        # find any pending submit that has not panicked
        for job in self.pending_submit.keys():
            if not job.parameters in self.panics:
                return True
        return False

    def no_pending(self) -> bool:
        for job in self:
            if job.parameters in self.panics:
                continue  # it is not pending, just panicked
            if job.pending_shots > 0:
                return False
        return True

    def load_from_file(
        self, filename: str, target_job: Optional[MonteCarloJob] = None
    ) -> None:
        if not os.path.exists(filename):
            return
        with portalocker.Lock(filename, "r") as f:
            persist = json.load(f)
            jobs = self.jobs.values() if target_job is None else [target_job]
            for job in jobs:
                if job.hash not in persist:
                    continue
                entry = persist[job.hash]
                # sanity check
                for entry_arg, arg in zip(entry["args"], job.args):
                    assert entry_arg == str(arg), "Hash conflict"
                assert entry["kwargs"].keys() == job.kwargs.keys(), "Hash conflict"
                for key in job.kwargs.keys():
                    assert entry["kwargs"][key] == str(job.kwargs[key]), "Hash conflict"
                # add to current value
                job.result = (
                    None
                    if entry["result"] is None
                    else self.result_type.from_dict(entry["result"])
                )
                job.finished_shots = entry["shots"]
                job.duration = entry["duration"]
                job.min_time = 0 if "min_time" not in entry else entry["min_time"]

    def update_file(self, filename: str) -> None:
        with portalocker.Lock(
            filename, "r+" if os.path.exists(filename) else "w+"
        ) as f:
            content = f.read()
            if content == "":
                persist = {}
            else:
                persist = json.loads(content)
            f.seek(0)
            for job in self.jobs.values():
                if job.hash not in persist:
                    persist[job.hash] = {
                        "args": [str(arg) for arg in job.args],
                        "kwargs": {
                            key: str(value) for key, value in job.kwargs.items()
                        },
                    }
                    entry = persist[job.hash]
                else:
                    entry = persist[job.hash]
                    # sanity check
                    for entry_arg, arg in zip(entry["args"], job.args):
                        assert entry_arg == str(arg), "Hash conflict"
                    assert entry["kwargs"].keys() == job.kwargs.keys(), "Hash conflict"
                    for key in job.kwargs.keys():
                        assert entry["kwargs"][key] == str(
                            job.kwargs[key]
                        ), "Hash conflict"
                # update value
                entry["result"] = (
                    job.result.to_dict() if job.result is not None else None
                )
                entry["shots"] = job.finished_shots
                entry["duration"] = job.duration
                entry["min_time"] = job.min_time
            json.dump(persist, f, indent=2)
            f.truncate()

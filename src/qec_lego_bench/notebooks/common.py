from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from qec_lego_bench.hpc.monte_carlo import MonteCarloResult, LogicalErrorResult
from qec_lego_bench.hpc.monte_carlo import *
import re
import numpy as np
import subprocess


def parametrized_decoder_of(decoder: str, **kwargs) -> str:
    if len(kwargs) == 0:
        return decoder
    if decoder[-1] == ")":
        prefix = decoder[:-1] + ","
    else:
        prefix = decoder + "("
    return prefix + ",".join([f"{key}={value}" for key, value in kwargs.items()]) + ")"


@dataclass_json(undefined="RAISE")  # avoid accidentally override other types
@dataclass
class MultiDecoderLogicalErrorRates:  # MonteCarloResult
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

    @property
    def average_elapsed(self) -> float:
        elapsed_vec = [
            result.elapsed
            for result in self.results.values()
            if result.elapsed is not None
        ]
        total_elapsed = sum(elapsed_vec)
        return total_elapsed / len(elapsed_vec)

    @property
    def min_elapsed(self) -> float:
        elapsed_vec = [
            result.elapsed
            for result in self.results.values()
            if result.elapsed is not None
        ]
        return min(elapsed_vec, default=0)


@dataclass_json(undefined="RAISE")  # avoid accidentally override other types
@dataclass
class FloatLogDistribution:  # MonteCarloResult
    lower: float = 1e-12
    upper: float = 1e12
    N: int = 4800
    counter: dict[int, int] = field(default_factory=lambda: {})
    underflow_count: int = 0
    overflow_count: int = 0  # including +inf, -inf and NaN

    def __post_init__(self):
        assert (
            float(f"{self.lower:.3e}") == self.lower
        ), f"accuracy loss after serialization: {self.lower}"
        assert (
            float(f"{self.upper:.3e}") == self.upper
        ), f"accuracy loss after serialization: {self.upper}"

    @staticmethod
    def from_line(line: str) -> "FloatLogDistribution":
        # example: "<lower>1.000e-9<upper>1.000e0<N>2000[666]1[695]23[696]80[698]7[699]3[underflow]0[overflow]0"
        match = re.search(
            r"<lower>([\+-e\d\.]+)<upper>([\+-e\d\.]+)<N>(\d+)((?:\[\d+\]\d+)*)\[underflow\](\d+)\[overflow\](\d+)",
            line,
        )
        assert match is not None
        lower = float(match.group(1))
        upper = float(match.group(2))
        N = int(match.group(3))
        counter = {}
        if match.group(4) != "":
            for ele in match.group(4)[1:].split("["):
                index, count = ele.split("]")
                counter[int(index)] = int(count)
        underflow_count = int(match.group(5))
        overflow_count = int(match.group(6))
        return FloatLogDistribution(
            lower=lower,
            upper=upper,
            N=N,
            counter=counter,
            underflow_count=underflow_count,
            overflow_count=overflow_count,
        )

    def load_trace(self, trace_filename: str) -> "FloatLogDistribution":
        data = np.fromfile(trace_filename, dtype=np.float32)
        for value in data[::4]:
            self.record(value)
        return self

    # the ratio between two latencies of neighboring bins
    @property
    def interval_ratio(self) -> float:
        return np.expm1(math.log(self.upper / self.lower) / self.N)

    def record(self, value: float, count: int = 1):
        if not np.isfinite(value):
            # also count NaN as infinite
            self.overflow_count += count
        if value < self.lower:
            self.underflow_count += count
        elif value >= self.upper:
            self.overflow_count += count
        else:
            ratio = math.log(value / self.lower) / math.log(self.upper / self.lower)
            index = math.floor(self.N * ratio)
            assert index < self.N
            if index in self.counter:
                self.counter[index] += count
            else:
                self.counter[index] = count

    def flatten(self) -> tuple[list[float], list[int]]:
        values = [
            self.lower * ((self.upper / self.lower) ** (i / self.N))
            for i in range(self.N)
        ]
        counters = [self.counter.get(i) or 0 for i in range(self.N)]
        counters[0] += self.underflow_count
        counters[1] += self.overflow_count
        return values, counters

    def to_line(self) -> str:
        line = f"<lower>{self.lower:.3e}<upper>{self.upper:.3e}<N>{self.N}"
        for index in sorted(self.counter.keys()):
            line += f"[{index}]{self.counter[index]}"
        line += f"[underflow]{self.underflow_count}[overflow]{self.overflow_count}"
        return line

    def assert_compatible_with(self, other: "FloatLogDistribution"):
        assert self.lower == other.lower
        assert self.upper == other.upper
        assert self.N == other.N

    def __add__(self, other: "FloatLogDistribution") -> "FloatLogDistribution":
        if self.count_records() == 0:
            return FloatLogDistribution(**other.__dict__)
        if other.count_records() == 0:
            return FloatLogDistribution(**self.__dict__)
        # if both are not empty, then they must be compatible before adding
        self.assert_compatible_with(other)
        result = FloatLogDistribution(**self.__dict__)
        result.underflow_count += other.underflow_count
        result.overflow_count += other.overflow_count
        for index in other.counter.keys():
            if index in result.counter:
                result.counter[index] += other.counter[index]
            else:
                result.counter[index] = other.counter[index]
        return result

    def value_of(self, index: int) -> float:
        return self.lower * ((self.upper / self.lower) ** ((index + 0.5) / self.N))

    def count_records(self) -> int:
        return sum(self.counter.values()) + self.underflow_count + self.overflow_count

    def average(self) -> float:
        sum_value = 0.0
        for index in self.counter.keys():
            sum_value += self.counter[index] * self.value_of(index)
        return sum_value / self.count_records()

    def filter_value_range(
        self, min_value: float, max_value: float, assert_count: int = 1
    ) -> "FloatLogDistribution":
        x_vec = []
        y_vec = []
        for value, count in zip(*self.flatten()):
            if value < min_value or value > max_value:
                assert (
                    count <= assert_count
                ), f"[warning] value {value} has count {count} > {assert_count}"
                continue
            x_vec.append(value)
            y_vec.append(count)
        distribution = FloatLogDistribution(
            lower=min(x_vec), upper=max(x_vec), N=len(x_vec)
        )
        for x, y in zip(x_vec, y_vec):
            distribution.record(x, y)
        return distribution

    # smooth the distribution by combing adjacent bins
    def combine_bins(self, combine_bin: int = 1) -> "FloatLogDistribution":
        x_vec, y_vec = self.flatten()
        cx_vec = []
        cy_vec = []
        if len(x_vec) % combine_bin != 0:
            # append 0 data
            padding = math.ceil(len(x_vec) / combine_bin) - len(x_vec)
            for i in range(padding):
                x = x_vec[-1] * (self.interval_ratio ** (1 + i))
                x_vec.append(x)
                y_vec.append(0)
        for idx in range(len(x_vec) // combine_bin):
            start = idx * combine_bin
            end = (idx + 1) * combine_bin
            x = sum(x_vec[start:end]) / combine_bin
            y = sum(y_vec[start:end])
            cx_vec.append(x)
            cy_vec.append(y)
        distribution = FloatLogDistribution(
            lower=min(cx_vec), upper=max(cx_vec), N=len(cx_vec)
        )
        for x, y in zip(cx_vec, cy_vec):
            distribution.record(x, y)
        return distribution

    def fit_exponential_tail(
        self, f_range: tuple[float, float] | None = None
    ) -> tuple[float, float]:
        counts_records = self.count_records()
        if f_range is None:
            f_range = (10 / counts_records, 1e5 / counts_records)
        min_f, max_f = f_range
        i_vec = []
        latencies, counters = self.flatten()
        # search from large value to small value
        for i, counter in reversed(list(enumerate(counters))):
            if counter / counts_records < min_f:
                continue
            if counter / counts_records >= max_f:
                break
            i_vec.append(i)
        fit_value = np.array([latencies[i] for i in i_vec])
        fit_freq = np.array([counters[i] for i in i_vec]) / counts_records

        # assume freq / (value * interval_ratio) = exp(A - B * value)
        fit_y = np.log(fit_freq) - np.log(fit_value) - np.log(self.interval_ratio)

        B, A = np.polyfit(-fit_value, fit_y, 1)
        # print(f"P(L) = exp({A} - {B} * value)")
        return A, B

    # find a value where accumulated probability beyond this value is higher than certain value
    def find_cut_off_value(self, probability: float) -> float:
        cut_off_count = self.count_records() * probability
        assert cut_off_count >= 10, "otherwise not accurate enough"
        # accumulate from right most
        x_vec, y_vec = self.flatten()
        accumulated = 0
        for idx in reversed(range(0, len(x_vec))):
            accumulated += y_vec[idx]
            if accumulated >= cut_off_count:
                return x_vec[idx + 1]
        return x_vec[0]


@dataclass_json(undefined="RAISE")  # avoid accidentally override other types
@dataclass
class DecodingTimeDistribution:  # MonteCarloResult
    elapsed: FloatLogDistribution = field(default_factory=FloatLogDistribution)
    result: LogicalErrorResult = field(default_factory=LogicalErrorResult)

    def __add__(self, other: "DecodingTimeDistribution") -> "DecodingTimeDistribution":
        return DecodingTimeDistribution(
            elapsed=self.elapsed + other.elapsed,
            result=self.result + other.result,
        )

    @property
    def errors(self) -> int:
        return self.result.errors

    @property
    def discards(self) -> int:
        return self.result.discards

    @property
    def panics(self) -> int:
        return self.result.panics

    def stats_of(self, job: "MonteCarloJob") -> Stats:
        return Stats(
            stats=sinter.AnonTaskStats(
                shots=job.shots,
                errors=self.errors,
                seconds=job.duration,
            ),
        )


@dataclass_json(undefined="RAISE")  # avoid accidentally override other types
@dataclass
class MultiDecoderDecodingTimeDistribution:  # MonteCarloResult
    results: dict[str, DecodingTimeDistribution] = field(default_factory=dict)

    def __add__(
        self, other: "MultiDecoderDecodingTimeDistribution"
    ) -> "MultiDecoderDecodingTimeDistribution":
        results = self.results.copy()
        for decoder, result in other.results.items():
            if decoder in results:
                results[decoder] += result
            else:
                results[decoder] = result
        return MultiDecoderDecodingTimeDistribution(results=results)

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


DEFAULT_SRUN_PREFIX: str = "srun --time=1-00:00:00 --mem=10G --cpus-per-task=2"
DEFAULT_SRUN_SUFFIX: str = ""


def papermill_execute_notebook(
    template_filepath: str,
    notebook_filepath: str,
    parameters: dict[str, Any],
    prepare_only: bool = False,
    no_progress_bar: bool = False,
    srun: bool = False,
    srun_prefix: str = DEFAULT_SRUN_PREFIX,
    srun_suffix: str = DEFAULT_SRUN_SUFFIX,
    srun_wait: bool = False,  # if not wait, output to jobout and joberr
):
    import papermill

    cwd = os.path.dirname(os.path.abspath(notebook_filepath))
    papermill.execute_notebook(
        template_filepath,
        notebook_filepath,
        parameters=parameters,
        prepare_only=prepare_only or srun,
        progress_bar=not no_progress_bar,
        cwd=cwd,
    )

    if srun and not prepare_only:
        command = (
            srun_prefix
            + f" papermill {notebook_filepath} {notebook_filepath} "
            + srun_suffix
        )
        print("[popen]", command)
        stdout = sys.stdout if srun_wait else open(f"z.{notebook_filepath}.jobout", "a")
        stderr = sys.stderr if srun_wait else open(f"z.{notebook_filepath}.joberr", "a")
        process = subprocess.Popen(
            command,
            shell=True,
            universal_newlines=True,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            cwd=cwd,
            close_fds=True,
            start_new_session=not srun_wait,
        )
        if srun_wait:
            process.wait()
        else:
            stdout.write(f"[popen] pid={process.pid}\n")
            stderr.write(f"[popen] pid={process.pid}\n")

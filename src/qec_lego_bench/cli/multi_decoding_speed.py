import arguably
from typing import Callable, Tuple, Optional
from sinter._decoding import sample_decode
from qec_lego_bench.decoders.profiling_decoder import ProfilingDecoder
from dataclasses_json import dataclass_json
from dataclasses import dataclass, field
from qec_lego_bench.cli.decoding_speed import DecodingSpeedResult
from qec_lego_bench.cli.generate_samples import generate_samples, benchmark_samples
from qec_lego_bench.hpc.monte_carlo import LogicalErrorResult
from qec_lego_bench.notebooks.common import MultiDecoderLogicalErrorRates
from .util import *
from .codes import *
from .noises import *
from .decoders import *
import tempfile
import os
import time

"""
Measure the actual decoding speed

Since some of the decoders don't implement sinter.CompiledDecoder and can suffer from slow start because of initialization,
we measure the time of the initialization and then remove that time from the evaluation.

All decoders will be forced to use the same `decode_via_files` method, as it is provided for every decoder.

When evaluating decoding speed, it is better to reduce the interference from the OS schedular.
```sh
papermill speed.ipynb zz-1.speed.ipynb  # run evaluation notebook in shell
ps -aux --sort=-pcpu | grep python  # find the PID of the jupyter kernal
sudo renice -n -20 -p <pid>
sudo taskset -pc 2,3,4,5 <pid>  # set the CPUs to run on (avoid overlapping with other evaluations)
```

"""


@arguably.command
def multi_decoding_speed(
    code: CodeCli,
    *,
    noise: NoiseCli = "NoNoise",  # type: ignore
    decoders: list[DecoderCli] | None = None,  # type: ignore
    min_shots: int = 10,
    max_shots: int = 10000000,
    min_time: float = 3 * 60,  # at least 3 minutes decoding
    no_print: bool = False,
    noise2: NoiseCli = "NoNoise",  # type: ignore
    noise3: NoiseCli = "NoNoise",  # type: ignore
) -> tuple[int, MultiDecoderLogicalErrorRates]:

    assert decoders is not None, "please provide a list of decoders"

    code = CodeCli(code)
    noise = NoiseCli(noise)
    decoders = [DecoderCli(d) for d in decoders]

    def decoding_task(shots: int) -> MultiDecoderLogicalErrorRates:

        start_time = time.time()

        with tempfile.TemporaryDirectory() as tmp_dir:
            filename = os.path.join(tmp_dir, "tmp")

            # check if any decoder requires decomposing errors, if so, use that decoder
            representative_decoder: DecoderCli = DecoderCli("none")
            for decoder in decoders:
                if decoder.decompose_errors:
                    representative_decoder = decoder
                    break

            generate_samples(
                code=code,
                filename=filename,
                noise=noise,
                noise2=noise2,
                noise3=noise3,
                shots=shots,
                decoder=representative_decoder,
                no_print=True,
            )

            results: dict[str, LogicalErrorResult] = {}
            for decoder in decoders:
                result = benchmark_samples(
                    filename=filename,
                    decoder=decoder,
                    no_print=True,
                    remove_initialization_time=True,
                )
                assert result.shots == shots
                results[str(decoder)] = LogicalErrorResult(
                    errors=result.errors, elapsed=result.elapsed
                )

        elapsed = time.time() - start_time

        if not no_print:
            sys.stdout.write("\r\033[K")
            print(
                f"Evaluating decoding of {shots} shots, elapsed: {elapsed:3f}s"
                + f", average: {elapsed/shots:.3e}s per shot",
                end="\r",
                flush=True,
            )
        return MultiDecoderLogicalErrorRates(results=results)

    shots, results = loop_time_evaluate(decoding_task, min_time, min_shots, max_shots)
    if not no_print:
        sys.stdout.write("\n")
        for decoder in decoders:
            elapsed: float | None = results.results[str(decoder)].elapsed
            if elapsed is None:
                print(f"[{str(decoder)}] decoding time: N/A")
                continue
            print(
                f"[{str(decoder)}] decoding time: {elapsed:.3e}s"
                + f", average: {elapsed / shots:.3e}s per shot",
            )

    return shots, results


def loop_time_evaluate(
    func: Callable[[int], MultiDecoderLogicalErrorRates],
    min_time: float,
    min_shots: int,
    max_shots: int,
) -> Tuple[int, MultiDecoderLogicalErrorRates]:
    shots = min_shots
    elapsed: Optional[float] = 0
    results: MultiDecoderLogicalErrorRates = MultiDecoderLogicalErrorRates()
    while shots <= max_shots or elapsed is None:
        results = func(shots)
        elapsed = results.min_elapsed
        if elapsed > min_time or shots >= max_shots:
            return shots, results
        if elapsed > 1:
            # use more accurate estimation
            ratio = 1.1 * min_time / elapsed
            ratio = max(ratio, 2)  # at least x2 every time to avoid stuck
            shots = min(int(shots * ratio), max_shots)
        else:
            shots = min(shots * 2, max_shots)
    return shots, results

import arguably
from typing import Callable, Tuple, Optional
from sinter._decoding import sample_decode
from qec_lego_bench.decoders.profiling_decoder import ProfilingDecoder
from dataclasses_json import dataclass_json
from dataclasses import dataclass
from .util import *
from .codes import *
from .noises import *
from .decoders import *

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


@dataclass_json
@dataclass
class DecodingSpeedResult:
    elapsed: float
    shots: int

    @property
    def decoding_time(self) -> float:
        return self.elapsed / self.shots


@arguably.command
def decoding_speed(
    code: CodeCli,
    *,
    noise: NoiseCli = "NoNoise",  # type: ignore
    decoder: DecoderCli = "mwpf",  # type: ignore
    min_init_time: float = 0.1,  # at least initialize the decoder for 100ms
    min_init_shots: int = 10,  # at least initialize the decoder for 10 times
    min_shots: int = 10,
    max_shots: int = 10000000,
    min_time: float = 3 * 60,  # at least 3 minutes decoding
    no_print: bool = False,
    noise2: NoiseCli = "NoNoise",  # type: ignore
    noise3: NoiseCli = "NoNoise",  # type: ignore
) -> DecodingSpeedResult:
    code_instance = CodeCli(code)()
    noise_instance = NoiseCli(noise)()
    noise2_instance = NoiseCli(noise2)()
    noise3_instance = NoiseCli(noise3)()
    decoder_instance = DecoderCli(decoder)()

    ideal_circuit = code_instance.circuit
    noisy_circuit = noise3_instance(noise2_instance(noise_instance(ideal_circuit)))

    circuit = noisy_circuit
    dem = noisy_circuit.detector_error_model(approximate_disjoint_errors=True)

    if hasattr(decoder_instance, "pass_circuit") and decoder_instance.pass_circuit:
        decoder_instance = decoder_instance.with_circuit(noisy_circuit)

    def initialization_task(shots: int) -> float:
        profiling_decoder = ProfilingDecoder(decoder_instance)
        for _ in range(shots):
            sample_decode(
                circuit_obj=circuit,
                circuit_path=None,
                dem_obj=dem,
                dem_path=None,
                num_shots=1,
                decoder=str(decoder),
                custom_decoders={str(decoder): profiling_decoder},
            )
        elapsed = profiling_decoder.elapsed
        if not no_print:
            sys.stdout.write("\r\033[K")
            print(
                f"Evaluating initialization of {shots} shots, elapsed: {elapsed:3f}s"
                + f", average: {elapsed/shots:.3e}s per shot",
                end="\r",
                flush=True,
            )
        return elapsed

    init_shots, init_elapsed = loop_time_evaluate(
        initialization_task, min_init_time, min_init_shots, max_shots
    )
    init_time = init_elapsed / init_shots
    if not no_print:
        sys.stdout.write("\n")
        print(f"initialization time: {init_time:.3e}s")

    # then evaluating real decoding time

    def decoding_task(shots: int) -> float:
        profiling_decoder = ProfilingDecoder(decoder_instance)
        sample_decode(
            circuit_obj=circuit,
            circuit_path=None,
            dem_obj=dem,
            dem_path=None,
            num_shots=shots + 1,
            decoder=str(decoder),
            custom_decoders={str(decoder): profiling_decoder},
        )
        elapsed = profiling_decoder.elapsed - init_time
        if not no_print:
            sys.stdout.write("\r\033[K")
            print(
                f"Evaluating decoding of {shots} shots, elapsed: {elapsed:3f}s"
                + f", average: {elapsed/shots:.3e}s per shot",
                end="\r",
                flush=True,
            )
        return elapsed

    shots, elapsed = loop_time_evaluate(decoding_task, min_time, min_shots, max_shots)
    decoding_time = elapsed / shots
    if not no_print:
        sys.stdout.write("\n")
        print(f"decoding time: {decoding_time:.3e}s")

    return DecodingSpeedResult(elapsed=elapsed, shots=shots)


def loop_time_evaluate(
    func: Callable[[int], float],
    min_time: float,
    min_shots: int,
    max_shots: int,
) -> Tuple[int, float]:
    shots = min_shots
    elapsed: Optional[float] = 0
    while shots <= max_shots or elapsed is None:
        elapsed = func(shots)
        if elapsed > min_time or shots >= max_shots:
            return shots, elapsed
        if elapsed > 1:
            # use more accurate estimation
            ratio = 1.1 * min_time / elapsed
            ratio = max(ratio, 2)  # at least x2 every time to avoid stuck
            shots = min(int(shots * ratio), max_shots)
        else:
            shots = min(shots * 2, max_shots)
    return shots, elapsed

import arguably
from typing import Callable, Tuple, Optional
from sinter._decoding import sample_decode
from qec_lego_bench.decoders.profiling_decoder import ProfilingDecoder
from dataclasses_json import dataclass_json
from dataclasses import dataclass
import stim
import tempfile
from .util import *
from .codes import *
from .noises import *
from .decoders import *
import tempfile
import hashlib
import os
from qec_lego_bench.codes.circuit_code import CircuitCode

"""
Generate a dem file and a b8 sample file, useful for decoding speed evaluation to test on exactly the same syndrome sequence.

If you want deterministic results, consider using a modified stim=1.15.0-dev version with sse disabled:
pip install git+https://github.com/yuewuo/Stim.git@stable-simulation
"""


@arguably.command
def generate_samples(
    code: CodeCli,
    filename: str,  # record the evaluation data of min_shots; it will generate a .dem file and a .b8 file separately
    *,
    noise: NoiseCli = "NoNoise",  # type: ignore
    shots: int = 10000,
    noise2: NoiseCli = "NoNoise",  # type: ignore
    noise3: NoiseCli = "NoNoise",  # type: ignore
    no_circuit: bool = False,
    no_dem: bool = False,
    no_samples: bool = False,
    mwpf_benchmark_suite: bool = False,
    decoder: DecoderCli = "mwpf",  # type: ignore
    seed: int | None = None,
):
    code_instance = CodeCli(code)()
    noise_instance = NoiseCli(noise)()
    noise2_instance = NoiseCli(noise2)()
    noise3_instance = NoiseCli(noise3)()

    ideal_circuit = code_instance.circuit
    noisy_circuit = noise3_instance(noise2_instance(noise_instance(ideal_circuit)))

    circuit = noisy_circuit

    if not no_circuit:
        circuit_filename = filename + ".stim"
        print("Writing Circuit file to", circuit_filename)
        circuit.to_file(circuit_filename)

    if not no_dem or not mwpf_benchmark_suite:
        dem_filename = filename + ".dem"
        print("Writing DEM file to", dem_filename)
        dem = noisy_circuit.detector_error_model(approximate_disjoint_errors=True)
        dem.to_file(dem_filename)
        num_dets = dem.num_detectors
        num_obs = dem.num_observables

    if not no_samples or not mwpf_benchmark_suite:
        det_filename = filename + ".det.b8"
        obs_filename = filename + ".obs.b8"
        print("Writing detectors to", det_filename, "and observables to", obs_filename)
        sampler: stim.CompiledDetectorSampler = circuit.compile_detector_sampler(
            seed=seed
        )
        sampler.sample_write(
            shots=shots,
            filepath=det_filename,
            format="b8",
            obs_out_filepath=obs_filename,
            obs_out_format="b8",
        )

    if mwpf_benchmark_suite:
        cbor_filename = filename + ".cbor"
        print("Writing Benchmark Suite file to", cbor_filename)
        decoder_instance = DecoderCli(decoder)()
        if hasattr(decoder_instance, "pass_circuit") and decoder_instance.pass_circuit:
            decoder_instance = decoder_instance.with_circuit(noisy_circuit)

        decoder_instance.benchmark_suite_filename = cbor_filename
        decoder_instance.decode_via_files(
            num_shots=shots,
            num_dets=num_dets,
            num_obs=num_obs,
            dem_path=dem_filename,
            dets_b8_in_path=det_filename,
            obs_predictions_b8_out_path=obs_filename,
            tmp_dir=tempfile.gettempdir(),
        )


@arguably.command
def benchmark_samples(
    filename: str,  # record the evaluation data of min_shots; it will generate a .dem file and a .b8 file separately
    *,
    max_shots: int | None = None,
    decoder: DecoderCli = "mwpf",  # type: ignore
) -> tuple[float, int]:
    circuit_filename = filename + ".stim"
    dem_filename = filename + ".dem"
    det_filename = filename + ".det.b8"
    # obs_filename = filename + ".obs.b8"

    code = CircuitCode(filepath=circuit_filename)
    decoder_instance = DecoderCli(decoder)()

    circuit = code.circuit

    if hasattr(decoder_instance, "pass_circuit") and decoder_instance.pass_circuit:
        decoder_instance = decoder_instance.with_circuit(circuit)

    num_dets = circuit.num_detectors
    num_obs = circuit.num_observables
    bytes_per_shot = (num_dets + 7) // 8
    det_bytes = os.path.getsize(det_filename)
    assert det_bytes % bytes_per_shot == 0, "inconsistent byte size"
    shots: int = det_bytes // bytes_per_shot

    profiling_decoder = ProfilingDecoder(decoder_instance)
    num_shots = shots if max_shots is None else min(shots, max_shots)
    with tempfile.TemporaryDirectory() as tmp_dir:
        profiling_decoder.decode_via_files(
            num_shots=num_shots,
            num_dets=num_dets,
            num_obs=num_obs,
            dem_path=dem_filename,
            dets_b8_in_path=det_filename,
            obs_predictions_b8_out_path=tmp_dir + "/predicted.b8",
            tmp_dir=tmp_dir,
        )
    elapsed = profiling_decoder.elapsed
    decoding_time = elapsed / num_shots

    print(
        f"decoding time: {decoding_time:.3e}s, elapsed: {elapsed:.3e}s, shots: {num_shots}"
    )

    return elapsed, num_shots


@arguably.command
def verify_deterministic_samples(*, quick: bool = False):
    code_noises = [
        (
            "bb(n=72,k=12,d=6)",
            "depolarize(p=0.01)",
            123,
            "333393ac20601ffb929a5cc922e2f58d",
            "f3c12542f4720c9ddf51013271970b82",
            "c1f824331742da4bbb33a969d61d7350",
        ),
        (
            "rsc(d=3,p=0.01)",
            "none",
            12,
            "8c037956acd5e847e2c8242f86b93692",
            "345433b8e1d4a862804fd8286fe8538a",
            "eaac8c1e695bac0e1209db21ad813e1c",
        ),
        (
            "color(d=3,p=0.01)",
            "erasure_conversion(rate=0.9)",
            6,
            "6401a1a84cebf7322e71f0d634204721",
            "647cf0041369c005b089014176024125",
            "f8b23f5cdb8e3a984014d329e6020b1b",
        ),
    ]
    if quick:
        code_noises = code_noises[:1]
    shots = 100
    success = True
    for code, noise, seed, circuit_md5, det_md5, obs_md5 in code_noises:
        print(f"==== running code={code}, noise={noise}, seed={seed} ====")
        with tempfile.NamedTemporaryFile() as tmp:
            generate_samples(code, tmp.name, noise=noise, shots=shots, seed=seed)
            circuit_file = tmp.name + ".stim"
            # dem file is intrinsically non-deterministic due to different floating point accuracy
            det_file = tmp.name + ".det.b8"
            obs_file = tmp.name + ".obs.b8"
            success &= check_md5(circuit_file, circuit_md5)
            success &= check_md5(det_file, det_md5)
            success &= check_md5(obs_file, obs_md5)
    if not success:
        raise Exception("Some md5s did not match")


def check_md5(filename: str, expected_md5: str) -> bool:
    with open(filename, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
        md5 = file_hash.hexdigest()
        if md5 != expected_md5:
            print(f"[error] md5 of {filename} is {md5} != {expected_md5}")
            return False
    return True

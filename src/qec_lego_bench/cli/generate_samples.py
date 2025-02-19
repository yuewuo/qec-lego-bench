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

"""
Generate a dem file and a b8 sample file, useful for decoding speed evaluation to test on exactly the same syndrome sequence.
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
        sampler: stim.CompiledDetectorSampler = circuit.compile_detector_sampler()
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

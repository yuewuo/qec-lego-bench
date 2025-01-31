import pathlib
import sinter
import time


class ProfilingDecoder(sinter.Decoder):
    def __init__(self, decoder: sinter.Decoder):
        self.elapsed = 0.0
        self.decoder = decoder

    def decode_via_files(
        self,
        *,
        num_shots: int,
        num_dets: int,
        num_obs: int,
        dem_path: pathlib.Path,
        dets_b8_in_path: pathlib.Path,
        obs_predictions_b8_out_path: pathlib.Path,
        tmp_dir: pathlib.Path,
    ) -> None:
        start = time.perf_counter()
        self.decoder.decode_via_files(
            num_shots=num_shots,
            num_dets=num_dets,
            num_obs=num_obs,
            dem_path=dem_path,
            dets_b8_in_path=dets_b8_in_path,
            obs_predictions_b8_out_path=obs_predictions_b8_out_path,
            tmp_dir=tmp_dir,
        )
        duration = time.perf_counter() - start
        self.elapsed += duration

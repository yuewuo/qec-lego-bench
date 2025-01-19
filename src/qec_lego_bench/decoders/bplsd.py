from qec_lego_bench.cli.decoders import decoder_cli
from typing import Optional
from dataclasses import dataclass
import pathlib
import sinter
from ldpc.sinter_decoders import SinterLsdDecoder


@decoder_cli("BPLSD", "BP_LSD")
@dataclass
class BPLSD(sinter.Decoder):

    # The maximum number of iterations for the decoding algorithm
    max_iter: int = 0

    # The belief propagation method used. Must be one of {'product_sum', 'minimum_sum'}
    bp_method: str = "ms"

    # The scaling factor used in the minimum sum method
    ms_scaling_factor: float = 0.625

    # The scheduling method used. Must be one of {'parallel', 'serial'}
    schedule: str = "parallel"

    # The number of OpenMP threads used for parallel decoding
    omp_thread_count: int = 1

    # A list of integers that specify the serial schedule order. Must be of length equal to the block length of the code
    serial_schedule_order: Optional[list[int]] = None

    lsd_order: int = 0

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
        decoder = SinterLsdDecoder(
            max_iter=self.max_iter,
            bp_method=self.bp_method,
            ms_scaling_factor=self.ms_scaling_factor,
            schedule=self.schedule,
            omp_thread_count=self.omp_thread_count,
            serial_schedule_order=self.serial_schedule_order,
            lsd_order=self.lsd_order,
        )
        return decoder.decode_via_files(
            num_shots=num_shots,
            num_dets=num_dets,
            num_obs=num_obs,
            dem_path=dem_path,
            dets_b8_in_path=dets_b8_in_path,
            obs_predictions_b8_out_path=obs_predictions_b8_out_path,
            tmp_dir=tmp_dir,
        )

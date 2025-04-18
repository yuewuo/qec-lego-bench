from qec_lego_bench.cli.decoders import decoder_cli
from typing import Optional
from dataclasses import dataclass
import pathlib
import sinter
from ldpc.sinter_decoders import SinterBpOsdDecoder


@decoder_cli("BPOSD", "BP_OSD")
@dataclass
class BPOSD(sinter.Decoder):

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

    # The OSD method used. Must be one of {'OSD_0', 'OSD_E', 'OSD_CS'}
    osd_method: str = "osd0"

    osd_order: int = 0  # The OSD order

    # by default BP may converge and directly return the result;
    # sometimes it's better if BP cannot directly return and always use the post-processing to decode
    bp_converge: bool = True

    # modified ldpc package at https://github.com/yuewuo/ldpc
    # format: 4 f32s for each iteration: elapsed, posterior_weight, prior_weight
    trace_filename: Optional[str] = None

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
        decoder = SinterBpOsdDecoder(
            max_iter=self.max_iter,
            bp_method=self.bp_method,
            ms_scaling_factor=self.ms_scaling_factor,
            schedule=self.schedule,
            omp_thread_count=self.omp_thread_count,
            serial_schedule_order=self.serial_schedule_order,
            osd_method=self.osd_method,
            osd_order=self.osd_order,
        )
        if self.trace_filename is not None:
            assert hasattr(
                decoder, "trace_filename"
            ), "please use custom version of bposd at https://github.com/yuewuo/ldpc"
            decoder.trace_filename = self.trace_filename
        if not self.bp_converge:
            assert hasattr(
                decoder, "bp_converge"
            ), "please use custom version of bposd at https://github.com/yuewuo/ldpc"
            decoder.bp_converge = self.bp_converge
        return decoder.decode_via_files(
            num_shots=num_shots,
            num_dets=num_dets,
            num_obs=num_obs,
            dem_path=dem_path,
            dets_b8_in_path=dets_b8_in_path,
            obs_predictions_b8_out_path=obs_predictions_b8_out_path,
            tmp_dir=tmp_dir,
        )

from qec_lego_bench.cli.decoders import decoder_cli
from typing import Optional
from dataclasses import dataclass
import pathlib
import sinter
from ldpc.sinter_decoders import SinterBeliefFindDecoder


@decoder_cli("BPUF", "BP_UF")
@dataclass
class BPUF(sinter.Decoder):

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

    # The method used to solve the local decoding problem in each cluster. Choose from: 1) 'inversion' or 2) 'peeling'.
    # By default set to 'inversion'. The 'peeling' method is only suitable for LDPC codes with point like syndromes.
    # The inversion method can be applied to any parity check matrix.
    uf_method: str = "inversion"

    # Specifies the number of bits added to the cluster in each step of the UFD algorithm. If no value is provided, this is set the block length of the code.
    bits_per_step: int = 0

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
        decoder = SinterBeliefFindDecoder(
            max_iter=self.max_iter,
            bp_method=self.bp_method,
            ms_scaling_factor=self.ms_scaling_factor,
            schedule=self.schedule,
            omp_thread_count=self.omp_thread_count,
            serial_schedule_order=self.serial_schedule_order,
            uf_method=self.uf_method,
            bits_per_step=self.bits_per_step,
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

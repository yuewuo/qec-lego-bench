from qec_lego_bench.cli.decoders import decoder_cli
from typing import Optional
from dataclasses import dataclass
import pathlib
import sinter
import stim
from sinter._decoding._decoding_mwpf import MwpfDecoder


@decoder_cli("MWPF", "mw_parity_factor")
@dataclass
class MWPF(sinter.Decoder):

    # The maximum number of nodes in each cluster; can be used to tune accuracy vs speed
    cluster_node_limit: int = 50

    def compile_decoder_for_dem(
        self,
        *,
        dem: stim.DetectorErrorModel,
    ) -> sinter.CompiledDecoder:
        return MwpfDecoder().compile_decoder_for_dem(
            dem=dem,
            cluster_node_limit=self.cluster_node_limit,
        )

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
        return MwpfDecoder().decode_via_files(
            num_shots=num_shots,
            num_dets=num_dets,
            num_obs=num_obs,
            dem_path=dem_path,
            dets_b8_in_path=dets_b8_in_path,
            obs_predictions_b8_out_path=obs_predictions_b8_out_path,
            tmp_dir=tmp_dir,
            cluster_node_limit=self.cluster_node_limit,
        )

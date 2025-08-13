from qec_lego_bench.cli.decoders import decoder_cli
from typing import Optional
from dataclasses import dataclass
import pathlib
import sinter
from relay_bp.stim import SinterDecoder_RelayBP
import numpy as np


@decoder_cli("RBP", "RelayBP")
@dataclass
class RelayBP(sinter.Decoder):

    alpha: Optional[float] = None
    gamma0: float = 0.1
    pre_iter: int = 60
    num_sets: int = 60
    set_max_iter: int = 60
    gamma_dist_interval_min: float = -0.24
    gamma_dist_interval_max: float = 0.66
    explicit_gammas: Optional[np.ndarray] = None
    stop_nconv: int = 5
    stopping_criterion: str = "nconv"
    logging: bool = False
    parallel: bool = False
    decomposed_hyperedges: Optional[bool] = None
    prune_decided_errors: bool = True
    threshold: float = 0.0

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
        decoder = SinterDecoder_RelayBP(
            alpha=self.alpha,
            gamma0=self.gamma0,
            pre_iter=self.pre_iter,
            num_sets=self.num_sets,
            set_max_iter=self.set_max_iter,
            gamma_dist_interval=(
                self.gamma_dist_interval_min,
                self.gamma_dist_interval_max,
            ),
            explicit_gammas=self.explicit_gammas,
            stop_nconv=self.stop_nconv,
            stopping_criterion=self.stopping_criterion,
            logging=self.logging,
            parallel=self.parallel,
            decomposed_hyperedges=self.decomposed_hyperedges,
            prune_decided_errors=self.prune_decided_errors,
            threshold=self.threshold,
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

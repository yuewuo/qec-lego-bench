import arguably
import stim
import sinter
from typing import Optional

from .util import *
from .codes import *
from .noises import *
from .decoders import *
from qec_lego_bench.stats import Stats


@arguably.command
def predict_on_disk(
    dem_path: str,
    dets_path: str,
    obs_out_path: str,
    *,
    # if None is provided instead of '01' or 'b8', it will infer based on the suffix
    dets_format: Optional[str] = None,
    obs_out_format: Optional[str] = None,
    postselect_detectors_with_non_zero_4th_coord: bool = False,
    discards_out_path: Optional[str] = None,
    discards_out_format: Optional[str] = None,
    decoder: DecoderCli = "mwpf",  # type: ignore
    actual_path: Optional[str] = None,
    actual_format: Optional[str] = None,
):
    decoder_instance = DecoderCli(decoder)()
    if dets_format is None:
        dets_format = infer_format(dets_path)
    if obs_out_format is None:
        obs_out_format = infer_format(obs_out_path)
    if discards_out_format is None and discards_out_path is not None:
        discards_out_format = infer_format(discards_out_path)
    if actual_format is None and actual_path is not None:
        actual_format = infer_format(actual_path)

    with open(dem_path) as f:
        dem = stim.DetectorErrorModel(f.read())
    dets = stim.read_shot_data_file(
        path=str(dets_path),
        format=dets_format,
        bit_pack=True,
        num_detectors=dem.num_detectors,
        num_observables=0,
    )
    shots = dets.shape[0]
    print(f"decoding {shots} shots...")

    sinter.predict_on_disk(
        decoder=str(decoder),
        dem_path=dem_path,
        dets_path=dets_path,
        dets_format=dets_format,
        obs_out_path=obs_out_path,
        obs_out_format=obs_out_format,
        postselect_detectors_with_non_zero_4th_coord=postselect_detectors_with_non_zero_4th_coord,
        discards_out_path=discards_out_path,
        discards_out_format=discards_out_format,
        custom_decoders={str(decoder): decoder_instance},
    )

    # if actual_path is not None:
    #     # print the logical error rate
    #     actual = stim.read_shot_data_file(
    #         path=str(actual_path),
    #         format=actual_format,
    #         bit_pack=True,
    #         num_detectors=0,
    #         num_observables=dem.num_obs,
    #     )
    #     predict = stim.read_shot_data_file(
    #         path=str(obs_out_path),
    #         format=obs_out_format,
    #         bit_pack=True,
    #         num_detectors=0,
    #         num_observables=dem.num_obs,
    #     )
    #     print(len(actual))
    #     print(len(predict))
    #     print(actual == predict)


def infer_format(path: str) -> str:
    if path.endswith(".01"):
        return "01"
    elif path.endswith(".b8"):
        return "b8"
    else:
        raise ValueError(f"Cannot infer format from path: {path}")

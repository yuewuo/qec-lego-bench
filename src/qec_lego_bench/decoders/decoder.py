from qec_lego_bench.cli.decoders import decoder_cli
from sinter._decoding._decoding_pymatching import PyMatchingDecoder
from sinter._decoding._decoding_fusion_blossom import FusionBlossomDecoder
from mwpf import SinterMWPFDecoder, SinterHUFDecoder, SinterSingleHairDecoder
from mwpf_rational import (
    SinterMWPFRationalDecoder,
    SinterHUFRationalDecoder,
    SinterSingleHairRationalDecoder,
)


decoder_cli("PyMatchingDecoder", "pymatching", "mwpm")(PyMatchingDecoder)
decoder_cli("FusionBlossomDecoder", "fusion_blossom", "fb")(FusionBlossomDecoder)

decoder_cli("MWPF", "mw_parity_factor")(SinterMWPFDecoder)
decoder_cli("HUF")(SinterHUFDecoder)
decoder_cli("MWPF_SH", "mwpfsh")(SinterSingleHairDecoder)

decoder_cli("MWPF_rational", "mwpfr")(SinterMWPFRationalDecoder)
decoder_cli("HUF_rational", "hufr")(SinterHUFRationalDecoder)
decoder_cli("MWPF_SH_rational", "mwpfshr")(SinterSingleHairRationalDecoder)

from qec_lego_bench.cli.decoders import decoder_cli
from sinter._decoding._decoding_pymatching import PyMatchingDecoder
from sinter._decoding._decoding_fusion_blossom import FusionBlossomDecoder
from mwpf import SinterMWPFDecoder, SinterHUFDecoder, SinterSingleHairDecoder


decoder_cli("PyMatchingDecoder", "pymatching", "mwpm")(PyMatchingDecoder)
decoder_cli("FusionBlossomDecoder", "fusion_blossom", "fb")(FusionBlossomDecoder)
decoder_cli("HUF")(SinterHUFDecoder)
decoder_cli("MWPF", "mw_parity_factor")(SinterMWPFDecoder)
decoder_cli("MWPF_SH")(SinterSingleHairDecoder)

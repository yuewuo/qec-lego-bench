from qec_lego_bench.cli.decoders import decoder_cli
from sinter._decoding._decoding_pymatching import PyMatchingDecoder
from sinter._decoding._decoding_fusion_blossom import FusionBlossomDecoder


decoder_cli("pymatching", "mwpm")(PyMatchingDecoder)
decoder_cli("fusion_blossom", "fb")(FusionBlossomDecoder)

from qec_lego_bench.cli.decoders import decoder_cli
from sinter._decoding._decoding_pymatching import PyMatchingDecoder
from sinter._decoding._decoding_fusion_blossom import FusionBlossomDecoder
from sinter._decoding._decoding_mwpf import MwpfDecoder


decoder_cli("PyMatchingDecoder", "pymatching", "mwpm")(PyMatchingDecoder)
decoder_cli("FusionBlossomDecoder", "fusion_blossom", "fb")(FusionBlossomDecoder)


@decoder_cli("HUF")
class HUF(MwpfDecoder):
    def __init__(self):
        super().__init__(cluster_node_limit=0)

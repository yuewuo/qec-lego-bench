from qec_lego_bench.cli.decoders import decoder_cli
from sinter._decoding._decoding_pymatching import PyMatchingDecoder
from sinter._decoding._decoding_fusion_blossom import FusionBlossomDecoder
from mwpf import SinterMWPFDecoder, SinterHUFDecoder


decoder_cli("PyMatchingDecoder", "pymatching", "mwpm")(PyMatchingDecoder)
decoder_cli("FusionBlossomDecoder", "fusion_blossom", "fb")(FusionBlossomDecoder)


@decoder_cli("HUF")
def huf_decoder() -> SinterHUFDecoder:
    return SinterHUFDecoder()


@decoder_cli("MWPF", "mw_parity_factor")
def mwpf_decoder(cluster_node_limit: int = 50) -> SinterMWPFDecoder:
    return SinterMWPFDecoder(cluster_node_limit=cluster_node_limit)

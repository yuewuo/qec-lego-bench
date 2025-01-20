from qec_lego_bench.cli.decoders import decoder_cli
import chromobius
from sinter._decoding._decoding_mwpf import MwpfDecoder


@decoder_cli("Chromobius", "cb")
def chromobius_decoder():
    return chromobius.sinter_decoders()["chromobius"]

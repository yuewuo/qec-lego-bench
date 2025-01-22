from qec_lego_bench.cli.decoders import decoder_cli
import chromobius


@decoder_cli("Chromobius", "cb")
def chromobius_decoder():
    return chromobius.sinter_decoders()["chromobius"]

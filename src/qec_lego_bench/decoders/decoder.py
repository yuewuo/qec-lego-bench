from qec_lego_bench.cli.decoders import decoder_cli
from sinter._decoding._decoding_pymatching import PyMatchingDecoder
from sinter._decoding._decoding_fusion_blossom import FusionBlossomDecoder
from sinter._decoding._decoding_vacuous import VacuousDecoder

decoder_cli("PyMatchingDecoder", "pymatching", "mwpm")(PyMatchingDecoder)
decoder_cli("FusionBlossomDecoder", "fusion_blossom", "fb", decompose_errors=True)(
    FusionBlossomDecoder
)
decoder_cli("VacuousDecoder", "none")(VacuousDecoder)

try:
    # the fast version is the default one for evaluation, but it may fail to import due to incompatibility with some platforms
    # it uses the gxhash library which requires AES-NI & SSE2 on X86 processors and AES & NEON on ARM processors
    # these hardware acceleration features are generally available on modern processors so here we use it as the default
    from mwpf_fast import (  # type: ignore
        SinterMWPFFastDecoder,
        SinterHUFFastDecoder,
        SinterSingleHairFastDecoder,
    )

    decoder_cli("MWPF", "mw_parity_factor")(SinterMWPFFastDecoder)
    decoder_cli("HUF")(SinterHUFFastDecoder)
    decoder_cli("MWPF_SH", "mwpfsh")(SinterSingleHairFastDecoder)
except BaseException as e:
    # print(e)
    pass

try:
    # the default version of mwpf is not as performant as the fast version, but at least it is platform independent
    from mwpf import SinterMWPFDecoder, SinterHUFDecoder, SinterSingleHairDecoder  # type: ignore

    decoder_cli("MWPF_default", "mwpfd")(SinterMWPFDecoder)
    decoder_cli("HUF_default", "hufd")(SinterHUFDecoder)
    decoder_cli("MWPF_SH_default", "mwpfshd")(SinterSingleHairDecoder)
except BaseException as e:
    # print(e)
    pass


try:
    from mwpf_rational import (  # type: ignore
        SinterMWPFRationalDecoder,
        SinterHUFRationalDecoder,
        SinterSingleHairRationalDecoder,
    )

    decoder_cli("MWPF_rational", "mwpfr")(SinterMWPFRationalDecoder)
    decoder_cli("HUF_rational", "hufr")(SinterHUFRationalDecoder)
    decoder_cli("MWPF_SH_rational", "mwpfshr")(SinterSingleHairRationalDecoder)
except BaseException as e:
    # print(e)
    pass


try:
    from mwpf_incr import (  # type: ignore
        SinterMWPFIncrDecoder,
        SinterHUFIncrDecoder,
        SinterSingleHairIncrDecoder,
    )

    decoder_cli("MWPF_incr", "mwpfi")(SinterMWPFIncrDecoder)
    decoder_cli("HUF_incr", "hufi")(SinterHUFIncrDecoder)
    decoder_cli("MWPF_SH_incr", "mwpfshi")(SinterSingleHairIncrDecoder)
except BaseException as e:
    # print(e)
    pass

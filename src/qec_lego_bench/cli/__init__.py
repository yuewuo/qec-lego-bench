import arguably
from .util import *
from . import logical_error_rate
from . import predict_on_disk
from . import decoding_speed
from . import generate_samples
from . import multi_decoding_speed
from qec_lego_bench import noises, decoders, codes, misc, notebooks


def run():
    arguably.run()


@arguably.command
def version(name: str):
    # print(f"Goodbye, {name}!")
    print(named_kwargs_of(name))


if __name__ == "__main__":
    run()

import arguably
from .util import *
from . import logical_error_rate
from qec_lego_bench import noises, decoders, codes


def run():
    arguably.run()


@arguably.command
def version(name: str):
    # print(f"Goodbye, {name}!")
    print(named_kwargs_of(name))


if __name__ == "__main__":
    run()

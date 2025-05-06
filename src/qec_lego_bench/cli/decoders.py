from .util import named_kwargs_of, params_of_func_or_cls
import sys
from typing import Union, Any
from functools import cached_property
from frozendict import frozendict

registered_decoder_names = {}
decompose_errors_decoders: set[str] = set()


def decoder_cli(*decoder_names: str, decompose_errors: bool = False):
    def decorator(constructor):
        params = params_of_func_or_cls(constructor)
        for decoder_name in decoder_names:
            assert decoder_name.isidentifier()
            decoder_name = decoder_name.lower()
            if decoder_name in registered_decoder_names:
                print(
                    f"[warning] decoder name {decoder_name} already registered",
                    file=sys.stderr,
                )
            registered_decoder_names[decoder_name] = (constructor, params)
            if decompose_errors:
                decompose_errors_decoders.add(decoder_name)
        return constructor

    return decorator


class DecoderCli:
    def __init__(self, input: Union[str, "DecoderCli"]):
        if isinstance(input, DecoderCli):
            self.input: str = input.input
            self.decoder: Any = input.decoder
            self.kwargs: dict = input.kwargs.copy()
            return
        try:
            self.input = input
            decoder_name, params = self.named_kwargs
            decoder_name = decoder_name.lower()
            if decoder_name not in registered_decoder_names:
                print(
                    f"[error] decoder name '{decoder_name}' not found, possible values: {', '.join(registered_decoder_names.keys())}",
                    file=sys.stderr,
                )
                raise ValueError()
            cls, expected_params = registered_decoder_names[decoder_name]
            self.kwargs = {}
            for param in params:
                assert (
                    param in expected_params
                ), f"unexpected parameter '{param}', expecting one of {', '.join(expected_params.keys())}"
                constructor = expected_params[param]
                self.kwargs[param] = constructor(params[param])
            self.decoder = cls(**self.kwargs)
        except Exception as e:
            print(f"[error] {e}", file=sys.stderr)
            raise e

    def __str__(self):
        return self.input

    def __call__(self):
        return self.decoder

    @cached_property
    def named_kwargs(self) -> tuple[str, frozendict[str, str]]:
        decoder_name, params = named_kwargs_of(self.input)
        return decoder_name, frozendict(params)

    @cached_property
    def decoder_name(self) -> str:
        decoder_name, _ = self.named_kwargs
        return decoder_name

    @cached_property
    def decompose_errors(self) -> bool:
        return self.decoder_name in decompose_errors_decoders

from .util import named_kwargs_of, params_of_func_or_cls
import sys

registered_decoder_names = {}


def decoder_cli(*decoder_names: str):
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
        return constructor

    return decorator


class DecoderCli:
    def __init__(self, input: str):
        try:
            self.input = input
            decoder_name, params = named_kwargs_of(input)
            decoder_name = decoder_name.lower()
            if decoder_name not in registered_decoder_names:
                print(
                    f"[error] decoder name '{decoder_name}' not found, possible values: {', '.join(registered_decoder_names.keys())}",
                    file=sys.stderr,
                )
                raise ValueError()
            cls, expected_params = registered_decoder_names[decoder_name]
            kwargs = {}
            for param in params:
                assert (
                    param in expected_params
                ), f"unexpected parameter '{param}', expecting one of {', '.join(expected_params.keys())}"
                constructor = expected_params[param]
                kwargs[param] = constructor(params[param])
            self.decoder = cls(**kwargs)
        except Exception as e:
            print(f"[error] {e}", file=sys.stderr)
            raise e

    def __str__(self):
        return self.input

    def __call__(self):
        return self.decoder

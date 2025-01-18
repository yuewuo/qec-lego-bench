from .util import named_kwargs_of, params_of_func_or_cls
import sys

registered_decoder_names = {}


def decoder_cli(decoder_name: str):
    def decorator(constructor):
        params = params_of_func_or_cls(constructor)
        if decoder_name in registered_decoder_names:
            print(
                f"[warning] decoder name {decoder_name} already registered",
                file=sys.stderr,
            )
        registered_decoder_names[decoder_name] = (constructor, params)

        def wrapper(*args, **kwargs):
            instance = constructor(*args, **kwargs)
            return instance

        return wrapper

    return decorator


class DecoderCli:
    def __init__(self, input: str):
        decoder_name, params = named_kwargs_of(input)
        if decoder_name not in registered_decoder_names:
            print(f"[error] decoder name '{decoder_name}' not found", file=sys.stderr)
            raise ValueError()
        cls, expected_params = registered_decoder_names[decoder_name]
        kwargs = {}
        for param in params:
            assert param in expected_params, f"unexpected parameter '{param}'"
            constructor = expected_params[param]
            kwargs[param] = constructor(params[param])
        try:
            self.decoder = cls(**kwargs)
        except Exception as e:
            print(f"[error] {e}", file=sys.stderr)
            raise e

    def __call__(self):
        return self.decoder

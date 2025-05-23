from .util import named_kwargs_of, params_of_func_or_cls
import sys
from typing import Union, Any

registered_noise_names = {}


def noise_cli(*noise_names: str):

    def decorator(constructor):
        params = params_of_func_or_cls(constructor)
        for noise_name in noise_names:
            assert noise_name.isidentifier()
            noise_name = noise_name.lower()
            if noise_name in registered_noise_names:
                print(
                    f"[warning] noise name {noise_name} already registered",
                    file=sys.stderr,
                )
            registered_noise_names[noise_name] = (constructor, params)

        return constructor

    return decorator


class NoiseCli:
    def __init__(self, input: Union[str, "NoiseCli"]):
        if isinstance(input, NoiseCli):
            self.input: str = input.input
            self.noise: Any = input.noise
            self.noise_name: str = input.noise_name
            self.kwargs: dict = input.kwargs.copy()
            return
        try:
            self.input = input
            noise_name, params = named_kwargs_of(input)
            noise_name = noise_name.lower()
            self.noise_name = noise_name
            if noise_name not in registered_noise_names:
                print(
                    f"[error] noise name '{noise_name}' not found, possible values: {', '.join(registered_noise_names.keys())}",
                    file=sys.stderr,
                )
                raise ValueError()
            cls, expected_params = registered_noise_names[noise_name]
            self.kwargs = {}
            for param in params:
                assert (
                    param in expected_params
                ), f"unexpected parameter '{param}', expecting one of {', '.join(expected_params.keys())}"
                constructor = expected_params[param]
                self.kwargs[param] = constructor(params[param])
            self.noise = cls(**self.kwargs)
        except Exception as e:
            print(f"[error] {e}", file=sys.stderr)
            raise e

    def __str__(self):
        return self.input

    def to_str(self) -> str:
        # try to mimic the input string but do not guarantee to be the same
        return f"{self.noise_name}({','.join([f'{k}={v}' for k, v in self.kwargs.items()])})"

    def __call__(self):
        return self.noise

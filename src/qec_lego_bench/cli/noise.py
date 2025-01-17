from .util import named_kwargs_of, params_of_func_or_cls
import sys

registered_noise_names = {}


def noise_cli(noise_name: str):
    def decorator(constructor):
        params = params_of_func_or_cls(constructor)
        if noise_name in registered_noise_names:
            print(
                f"[warning] noise name {noise_name} already registered", file=sys.stderr
            )
        registered_noise_names[noise_name] = (constructor, params)

        def wrapper(*args, **kwargs):
            instance = constructor(*args, **kwargs)
            return instance

        return wrapper

    return decorator


class NoiseCli:
    def __init__(self, input: str):
        noise_name, params = named_kwargs_of(input)
        if noise_name not in registered_noise_names:
            print(f"[error] noise name '{noise_name}' not found", file=sys.stderr)
            raise ValueError()
        cls, expected_params = registered_noise_names[noise_name]
        kwargs = {}
        for param in params:
            assert param in expected_params, f"unexpected parameter '{param}'"
            constructor = expected_params[param]
            kwargs[param] = constructor(params[param])
        try:
            self.noise = cls(**kwargs)
        except Exception as e:
            print(f"[error] {e}", file=sys.stderr)
            raise e

    def __call__(self):
        return self.noise

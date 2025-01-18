from .util import named_kwargs_of, params_of_func_or_cls
import sys

registered_code_names = {}


def code_cli(code_name: str):
    def decorator(constructor):
        params = params_of_func_or_cls(constructor)
        if code_name in registered_code_names:
            print(
                f"[warning] code name {code_name} already registered", file=sys.stderr
            )
        registered_code_names[code_name] = (constructor, params)

        def wrapper(*args, **kwargs):
            instance = constructor(*args, **kwargs)
            return instance

        return wrapper

    return decorator


class CodeCli:
    def __init__(self, input: str):
        code_name, params = named_kwargs_of(input)
        if code_name not in registered_code_names:
            print(
                f"[error] code name '{code_name}' not found, possible values: {', '.join(registered_code_names.keys())}",
                file=sys.stderr,
            )
            raise ValueError()
        cls, expected_params = registered_code_names[code_name]
        kwargs = {}
        for param in params:
            assert param in expected_params, f"unexpected parameter '{param}'"
            constructor = expected_params[param]
            kwargs[param] = constructor(params[param])
        try:
            self.code = cls(**kwargs)
        except Exception as e:
            print(f"[error] {e}", file=sys.stderr)
            raise e

    def __call__(self):
        return self.code

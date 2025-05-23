from .util import named_kwargs_of, params_of_func_or_cls
from typing import Union, Any
import sys

registered_code_names = {}


def code_cli(*code_names: str):
    def decorator(constructor):
        params = params_of_func_or_cls(constructor)
        for code_name in code_names:
            assert code_name.isidentifier()
            code_name = code_name.lower()
            if code_name in registered_code_names:
                print(
                    f"[warning] code name {code_name} already registered",
                    file=sys.stderr,
                )
            registered_code_names[code_name] = (constructor, params)
        return constructor

    return decorator


class CodeCli:
    def __init__(self, input: Union[str, "CodeCli"]):
        if isinstance(input, CodeCli):
            self.input: str = input.input
            self.code: Any = input.code
            self.code_name: str = input.code_name
            self.kwargs: dict = input.kwargs.copy()
            return
        try:
            self.input = input
            code_name, params = named_kwargs_of(input)
            code_name = code_name.lower()
            self.code_name = code_name
            if code_name not in registered_code_names:
                print(
                    f"[error] code name '{code_name}' not found, possible values: {', '.join(registered_code_names.keys())}",
                    file=sys.stderr,
                )
                raise ValueError()
            cls, expected_params = registered_code_names[code_name]
            self.kwargs = {}
            for param in params:
                assert (
                    param in expected_params
                ), f"unexpected parameter '{param}', expecting one of {', '.join(expected_params.keys())}"
                constructor = expected_params[param]
                self.kwargs[param] = constructor(params[param])
            self.code = cls(**self.kwargs)
        except Exception as e:
            print(f"[error] {e}", file=sys.stderr)
            raise e

    def __str__(self):
        return self.input

    def to_str(self) -> str:
        # try to mimic the input string but do not guarantee to be the same
        return f"{self.code_name}({','.join([f'{k}={v}' for k, v in self.kwargs.items()])})"

    def __call__(self):
        return self.code

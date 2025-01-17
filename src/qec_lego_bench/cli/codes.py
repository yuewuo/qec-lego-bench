from .util import named_kwargs_of
import inspect
import sys
import types

registered_code_names = {}


def code_cli(code_name: str):
    def decorator(func):
        """
        the decorated class must have an initialization function that accepts str, int or float KEYWORD input.
        All other types of input must be convertible from str, i.e., cls(str) must work
        """
        signature = inspect.signature(func)
        params = {}
        for param in list(signature.parameters.values()):
            if isinstance(param.annotation, types.UnionType):
                args = [arg for arg in param.annotation.__args__ if arg != type(None)]
                assert len(args) == 1, "only support Union[TYPE, None] for now"
                assert (
                    param.default is None
                ), f"default value of {param.name} must be None for Union[TYPE, None] in {func.__name__}"
                params[param.name] = args[0]
            else:
                params[param.name] = param.annotation
        if code_name in registered_code_names:
            print(
                f"[warning] code name {code_name} already registered", file=sys.stderr
            )
        registered_code_names[code_name] = (func, params)

        def wrapper(*args, **kwargs):
            instance = func(*args, **kwargs)
            return instance

        return wrapper

    return decorator


class CodeCli:
    def __init__(self, input: str):
        code_name, params = named_kwargs_of(input)
        if code_name not in registered_code_names:
            print(f"[error] code name '{code_name}' not found", file=sys.stderr)
            raise ValueError()
        cls, expected_params = registered_code_names[code_name]
        kwargs = {}
        for param in params:
            assert param in expected_params, f"unexpected parameter '{param}'"
            constructor = expected_params[param]
            kwargs[param] = constructor(params[param])
        try:
            self.code = cls(**kwargs)
            print(self.code)
        except Exception as e:
            print(f"[error] {e}", file=sys.stderr)
            raise e

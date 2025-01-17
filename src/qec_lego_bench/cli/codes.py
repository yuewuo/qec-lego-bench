from .util import named_kwargs_of
import inspect
import sys

registered_code_cli = {}


def code_cli(code_name: str):
    def decorator(cls):
        """
        the decorated class must have an initialization function that accepts str, int or float KEYWORD input.
        All other types of input must be convertible from str, i.e., cls(str) must work
        """
        signature = inspect.signature(cls.__init__)
        params = {}
        for param in list(signature.parameters.values())[1:]:
            params[param.name] = param.annotation
        if code_name in registered_code_cli:
            print(
                f"[warning] code name {code_name} already registered", file=sys.stderr
            )
        registered_code_cli[code_name] = (cls, params)

        def wrapper(*args, **kwargs):
            instance = cls(*args, **kwargs)
            return instance

        return wrapper

    return decorator


class CodeCli:
    def __init__(self, input: str):
        print(named_kwargs_of(input))

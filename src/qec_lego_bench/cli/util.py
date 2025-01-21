from typing import Any
import typing
from urllib.parse import parse_qs
import inspect
import types


def kwargs_of_qs(qs: str) -> dict[str, str]:
    """
    parsing a custom querystring format into a dictionary.
    The format is normal querystring format, but with '&' replaced by ','.
    Thus, the value cannot contain ',', which is usually fine in the context of this project.
    """
    querystring = qs.replace(",", "&")
    dict_of_qs = parse_qs(querystring)
    assert len(dict_of_qs) > 0 or qs == "", f"querystring '{qs}' is not valid"
    for key in dict_of_qs:
        assert key.isidentifier(), f"key '{key}' is not a valid identifier"
    return {key: value[0] for key, value in dict_of_qs.items()}


def named_kwargs_of(input: str) -> tuple[str, dict[str, str]]:
    """
    expecting a format of 'name(a=1,b=2)'
    """
    if "(" in input:
        assert input[-1] == ")"
        split_index = input.index("(")
        name = input[:split_index]
        assert name.isidentifier(), f"name '{name}' is not a valid identifier"
        kwargs = kwargs_of_qs(input[split_index + 1 : -1])
        return name, kwargs
    name = input
    assert name.isidentifier(), f"name '{name}' is not a valid identifier"
    return name, {}


def params_of_func_or_cls(func: Any) -> dict[str, Any]:
    """
    the decorated class must have an initialization function that accepts str, int or float KEYWORD input.
    or it could be a function that accepts str, int or float KEYWORD input.
    All other types of arguments must be convertible from str, i.e., cls(str) must work
    """
    signature = inspect.signature(func)
    params = {}
    for param in list(signature.parameters.values()):
        if (
            isinstance(param.annotation, types.UnionType)
            or typing.get_origin(param.annotation) == typing.Union
        ):
            args = [arg for arg in param.annotation.__args__ if arg != type(None)]
            assert len(args) == 1, "only support Union[TYPE, None] for now"
            assert (
                param.default is None
            ), f"default value of {param.name} must be None for Union[TYPE, None] in {func.__name__}"
            params[param.name] = args[0]
        else:
            params[param.name] = param.annotation
    return params

from typing import Any, Type, Callable
import typing
from urllib.parse import parse_qs
import inspect
import types
from enum import Enum


def kwargs_of_qs(qs: str) -> dict[str, str]:
    """
    parsing a custom querystring format into a dictionary.
    The format is normal querystring format, but with '&' replaced by ',' or ';'.
    Thus, the value cannot contain ',' or ';', which is usually fine in the context of this project.
    Optionally, one can use '@' as an alias to '=' to avoid issues when '=' has special meanings (e.g. in papermill).
    """
    querystring = qs.replace(",", "&").replace(";", "&").replace("@", "=")
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
        assert (
            input[-1] == ")"
        ), f"input '{input}' is not a valid format, consider using ; in lieu of ,"
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
        elif param.annotation == bool:
            params[param.name] = bool_constructor
        elif inspect.isclass(param.annotation) and issubclass(param.annotation, Enum):
            params[param.name] = enum_constructor_of(param.annotation)
        else:
            params[param.name] = param.annotation
    return params


def bool_constructor(name: str) -> bool:
    if name.lower() == "true" or name == "1":
        return True
    if name.lower() == "false" or name == "0":
        return False
    return bool(name)


def enum_constructor_of(enum_class: Type[Enum]) -> Callable[[str], Enum]:
    supported_names = {e.name: e for e in enum_class}

    def constructor(name: str) -> Enum:
        if name not in supported_names:
            raise ValueError(
                f"enum name {name} not in supported names: {list(supported_names.keys())}"
            )
        return supported_names[name]

    return constructor

from typing import Any
from urllib.parse import parse_qs


def kwargs_of_qs(qs: str) -> dict[str, str]:
    """
    parsing a custom querystring format into a dictionary.
    The format is normal querystring format, but with '&' replaced by ','.
    Thus, the value cannot contain ',', which is usually fine in the context of this project.
    """
    querystring = qs.replace(",", "&")
    dict_of_qs = parse_qs(querystring)
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

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

# Registry: model class -> human formatter function
_human_formatters: dict[type, Any] = {}


def human_formatter(model_cls: type):
    """Register a human-readable formatter for a pydantic model class.

    Usage::

        @human_formatter(MyModel)
        def format_my_model(model: MyModel) -> str:
            return f"{model.name}: {model.value}"
    """

    def decorator(func):
        _human_formatters[model_cls] = func
        return func

    return decorator


def render(data: Any, *, human: bool = False) -> None:
    """Render data to stdout as JSON or human-readable text.

    Parameters
    ----------
    data
        A pydantic BaseModel, list of BaseModels, or dict.
    human
        If True, use registered human formatters (fallback to JSON).
    """
    if human:
        text = _format_human(data)
        print(text)
    else:
        text = _format_json(data)
        print(text)


def _format_json(data: Any) -> str:
    if isinstance(data, BaseModel):
        return data.model_dump_json(indent=2, exclude_none=True)
    if isinstance(data, list) and data and isinstance(data[0], BaseModel):
        return json.dumps(
            [item.model_dump(exclude_none=True) for item in data],
            indent=2,
        )
    return json.dumps(data, indent=2)


def _format_human(data: Any) -> str:
    if isinstance(data, BaseModel):
        formatter = _human_formatters.get(type(data))
        if formatter:
            return formatter(data)
        return _format_json(data)

    if isinstance(data, list) and data and isinstance(data[0], BaseModel):
        formatter = _human_formatters.get(type(data[0]))
        if formatter:
            return "\n\n".join(formatter(item) for item in data)
        return _format_json(data)

    return _format_dict_human(data)


def _format_dict_human(data: Any, indent: int = 0) -> str:
    lines: list[str] = []
    prefix = "  " * indent
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{prefix}{k}:")
                lines.append(_format_dict_human(v, indent + 1))
            else:
                lines.append(f"{prefix}{k}: {v}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                lines.append(_format_dict_human(item, indent))
                lines.append("")
            else:
                lines.append(f"{prefix}- {item}")
    else:
        lines.append(f"{prefix}{data}")
    return "\n".join(lines)

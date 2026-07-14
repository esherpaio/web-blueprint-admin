from typing import Any, Callable

from web.app.urls import url_for

from .enums import Style


def resolve_path(obj: Any, path: str) -> Any:
    value = obj
    for part in path.split("."):
        if value is None:
            return None
        value = getattr(value, part, None)
    return value


def resolve_value(value: Any, obj: Any) -> Any:
    return value(obj) if callable(value) else value


def resolve_href(
    obj: Any,
    *,
    endpoint: str | None,
    url: str | Callable[[Any], str] | None,
    values: dict[str, Any] | Callable[[Any], dict[str, Any]] | None,
) -> str | None:
    if url is not None:
        return url(obj) if callable(url) else url
    if endpoint is not None:
        resolved = values(obj) if callable(values) else (values or {})
        return url_for(endpoint, **resolved)
    return None


def capfirst(text: str | None) -> str:
    if not text:
        return ""
    return text[0].upper() + text[1:]


def default_label(name: str) -> str:
    base = name[:-3] if name.endswith("_id") else name
    return capfirst(base.replace("_", " ").strip())


def button_class(style: str | None = Style.PRIMARY, size: str | None = None) -> str:
    parts = ["btn"]
    if size:
        parts.append(f"btn-{size}")
    if style:
        parts.append(f"btn-{style}")
    return " ".join(parts)

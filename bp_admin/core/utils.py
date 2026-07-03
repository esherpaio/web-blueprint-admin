from typing import Any, Callable

from web.app.urls import url_for


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


def default_label(name: str) -> str:
    base = name[:-3] if name.endswith("_id") else name
    return base.replace("_", " ").strip().capitalize()

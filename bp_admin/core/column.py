from typing import Any, Callable

from markupsafe import Markup, escape
from web.app.urls import url_for

from .field import Field, StringField, default_label


def getattr_path(obj: Any, path: str) -> Any:
    value = obj
    for part in path.split("."):
        if value is None:
            return None
        value = getattr(value, part, None)
    return value


def row_input_name(row_id: Any, name: str) -> str:
    return f"rows-{row_id}-{name}"


class Column:
    def __init__(
        self,
        name: str,
        label: str | None = None,
        *,
        editable: bool = False,
        field: Field | None = None,
        format: str | Callable[[Any], Any] | None = None,
        row_format: Callable[[Any], Any] | None = None,
        align: str | None = None,
    ) -> None:
        self.name = name
        self.label = label if label is not None else default_label(name)
        self.editable = editable
        self.field = field if field is not None else StringField(name)
        self.format = format
        self.row_format = row_format
        self.align = align

    @property
    def format_name(self) -> str | None:
        return self.format if isinstance(self.format, str) else None

    @property
    def align_class(self) -> str:
        return f"text-{self.align}" if self.align else ""

    def value(self, obj: Any) -> Any:
        return getattr_path(obj, self.name)

    def input_name(self, row_id: Any) -> str:
        return row_input_name(row_id, self.name)

    def cell_value(self, obj: Any, form_values: Any) -> Any:
        submitted = form_values.get(self.input_name(obj.id))
        return submitted if submitted is not None else self.field.value_from_obj(obj)

    def display(self, obj: Any) -> Any:
        if self.row_format is not None:
            return self.row_format(obj)
        value = self.value(obj)
        if callable(self.format):
            return self.format(value)
        return value


class Link:
    def __init__(
        self,
        label: str | Callable[[Any], str],
        *,
        endpoint: str | None = None,
        url: str | Callable[[Any], str] | None = None,
        values: dict[str, Any] | Callable[[Any], dict[str, Any]] | None = None,
        target: str | None = None,
        download: bool = False,
        style: str = "primary",
        size: str | None = "sm",
        icon: str | None = None,
        mode: str = "button",
        visible: Callable[[Any], bool] | None = None,
    ) -> None:
        self.label = label
        self.endpoint = endpoint
        self.url = url
        self.values = values
        self.target = target
        self.download = download
        self.style = style
        self.size = size
        self.icon = icon
        self.mode = mode
        self._visible = visible

    def is_visible(self, obj: Any = None) -> bool:
        return self._visible(obj) if self._visible is not None else True

    def href(self, obj: Any = None) -> str | None:
        if self.url is not None:
            return self.url(obj) if callable(self.url) else self.url
        if self.endpoint is not None:
            values = self.values(obj) if callable(self.values) else (self.values or {})
            return url_for(self.endpoint, **values)
        return None

    def render(self, obj: Any = None) -> Markup:
        if not self.is_visible(obj):
            return Markup("")
        href = self.href(obj)
        if not href:
            return Markup("")
        label = self.label(obj) if callable(self.label) else self.label
        target = (
            f' target="{escape(self.target)}" rel="noopener"' if self.target else ""
        )
        download = " download" if self.download else ""
        icon = f'<i class="bi {escape(self.icon)} me-1"></i>' if self.icon else ""
        if self.mode == "text":
            return Markup(
                f'<a href="{escape(href)}"{target}{download}>{icon}{escape(label)}</a>'
            )
        size = f"btn-{self.size} " if self.size else ""
        return Markup(
            f'<a class="btn {size}btn-{self.style}" '
            f'href="{escape(href)}"{target}{download}>{icon}{escape(label)}</a>'
        )


class LinkColumn(Column):
    def __init__(
        self,
        name: str,
        label: str | None = "",
        *,
        link: Link,
        align: str | None = None,
    ) -> None:
        super().__init__(name, label, align=align)
        self.link = link

    def display(self, obj: Any) -> Any:
        return self.link.render(obj)

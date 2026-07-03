from typing import Any, Callable

from .field import Field, StringField
from .utils import default_label, resolve_href, resolve_path, resolve_value


def row_input_name(row_id: Any, name: str) -> str:
    return f"rows-{row_id}-{name}"


class Column:
    is_link = False

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
        return resolve_path(obj, self.name)

    def input_name(self, row_id: Any) -> str:
        return row_input_name(row_id, self.name)

    def cell_value(self, obj: Any, form_values: Any) -> Any:
        submitted = form_values.get(self.input_name(obj.id))
        if submitted is not None:
            return submitted
        return self.field.value_from_obj(obj)

    def display(self, obj: Any) -> Any:
        if self.row_format is not None:
            return self.row_format(obj)
        value = self.value(obj)
        if callable(self.format):
            return self.format(value)
        return value


class LinkColumn(Column):
    is_link = True

    def __init__(
        self,
        name: str,
        label: str | None = "",
        *,
        text: str | Callable[[Any], str],
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
        align: str | None = None,
    ) -> None:
        super().__init__(name, label, align=align)
        self._text = text
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
        if self._visible:
            return self._visible(obj)
        return True

    def href(self, obj: Any) -> str | None:
        return resolve_href(
            obj,
            endpoint=self.endpoint,
            url=self.url,
            values=self.values,
        )

    def text(self, obj: Any) -> str:
        return resolve_value(self._text, obj)

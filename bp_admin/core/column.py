"""List-table columns for the declarative admin engine.

A :class:`Column` describes one cell in a list/inline table. It can be a plain
read-only display cell or an inline-editable cell backed by a :class:`Field`.
"""

from typing import Any, Callable

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
    """A single list-table column.

    ``format`` is either one of the names understood by ``display_cell``
    (``"price"``, ``"datetime"``, ``"bool"``) or a callable that turns the raw
    value into a display value.
    """

    def __init__(
        self,
        name: str,
        label: str | None = None,
        *,
        editable: bool = False,
        field: Field | None = None,
        format: str | Callable[[Any], Any] | None = None,
        align: str | None = None,
    ) -> None:
        self.name = name
        self.label = label if label is not None else default_label(name)
        self.editable = editable
        self.field = field if field is not None else StringField(name)
        self.format = format
        self.align = align

    @property
    def format_name(self) -> str | None:
        return self.format if isinstance(self.format, str) else None

    def value(self, obj: Any) -> Any:
        return getattr_path(obj, self.name)

    def input_name(self, row_id: Any) -> str:
        return row_input_name(row_id, self.name)

    def cell_value(self, obj: Any, form_values: Any) -> Any:
        submitted = form_values.get(self.input_name(obj.id))
        return submitted if submitted is not None else self.field.value_from_obj(obj)

    def display(self, obj: Any) -> Any:
        value = self.value(obj)
        if callable(self.format):
            return self.format(value)
        return value

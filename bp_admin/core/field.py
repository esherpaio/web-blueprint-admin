"""Form fields for the declarative admin engine.

A :class:`Field` is a small, declarative description of a single editable value.
It knows three things:

* how to read its current value from a model instance (:meth:`value_from_obj`),
* how to coerce a raw submitted value into a Python value (:meth:`parse`),
* enough metadata for the macros in ``_macros.html`` to render the input.

Rendering itself lives in the templates; fields stay logic-only so they remain
easy to test and reason about.
"""

import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Sequence

from sqlalchemy.orm.session import Session

from .enums import AttrType, InputType

Choice = tuple[Any, str]
ChoiceProvider = Sequence[Choice] | Callable[[Session], Sequence[Choice]]


def default_label(name: str) -> str:
    base = name[:-3] if name.endswith("_id") else name
    return base.replace("_", " ").strip().capitalize()


class Field:
    """Base field. Renders as a single-line text input by default."""

    input_type = InputType.TEXT

    def __init__(
        self,
        name: str,
        label: str | None = None,
        *,
        required: bool = False,
        readonly: bool = True,
        placeholder: str | None = None,
        attrs: dict[str, Any] | None = None,
        suffix: str | None = None,
    ) -> None:
        self.name = name
        self.label = label if label is not None else default_label(name)
        self.required = required
        self.readonly = readonly
        self.placeholder = placeholder
        self.attrs = attrs or {}
        self.suffix = suffix

    @property
    def col_class(self) -> str:
        if self.input_type in (InputType.TEXTAREA, InputType.ATTRIBUTES):
            return "col-12"
        return "col-12 col-lg-6"

    @property
    def html_input_type(self) -> str:
        if self.input_type == InputType.DATETIME:
            return "datetime-local"
        return self.input_type

    #
    # Reading
    #

    def value_from_obj(self, obj: Any) -> Any:
        return getattr(obj, self.name, None)

    def form_value(self, obj: Any, form_values: Any) -> Any:
        submitted = form_values.get(self.name)
        return submitted if submitted is not None else self.value_from_obj(obj)

    def choices(self, s: Session) -> list[Choice]:
        return []

    #
    # Writing
    #

    def parse(self, form: Any, files: Any = None, name: str | None = None) -> Any:
        raw = form.get(name or self.name)
        return self._coerce(raw)

    def apply(self, obj: Any, value: Any) -> None:
        setattr(obj, self.name, value)

    def _coerce(self, raw: Any) -> Any:
        if raw is None:
            return None
        raw = raw.strip() if isinstance(raw, str) else raw
        return raw if raw != "" else None


class StringField(Field):
    input_type = InputType.TEXT


class TextAreaField(Field):
    input_type = InputType.TEXTAREA

    def __init__(self, *args: Any, rows: int = 3, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.rows = rows


class IntegerField(Field):
    input_type = InputType.NUMBER

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("attrs", {}).setdefault("step", "1")
        super().__init__(*args, **kwargs)

    def _coerce(self, raw: Any) -> int | None:
        if raw is None or raw == "":
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None


class PercentageField(IntegerField):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("suffix", "%")
        super().__init__(*args, **kwargs)

    def value_from_obj(self, obj: Any) -> int | None:
        if obj.rate is None:
            return None
        return int(round((1 - obj.rate) * 100))

    def apply(self, obj: Any, value: Any) -> None:
        if value is None:
            return
        obj.rate = Decimal("1") - (Decimal(value) / Decimal("100"))


class DecimalField(Field):
    input_type = InputType.NUMBER

    def __init__(self, *args: Any, step: str = "0.01", **kwargs: Any) -> None:
        kwargs.setdefault("attrs", {}).setdefault("step", step)
        super().__init__(*args, **kwargs)

    def _coerce(self, raw: Any) -> Decimal | None:
        if raw is None or raw == "":
            return None
        try:
            return Decimal(str(raw))
        except (TypeError, ValueError, InvalidOperation):
            return None


class BoolField(Field):
    input_type = InputType.CHECKBOX

    def parse(self, form: Any, files: Any = None, name: str | None = None) -> bool:
        return (name or self.name) in form


class SelectField(Field):
    input_type = InputType.SELECT

    def __init__(
        self,
        name: str,
        label: str | None = None,
        *,
        choices: ChoiceProvider = (),
        coerce: Callable[[Any], Any] | None = None,
        empty_label: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(name, label, **kwargs)
        self._choices = choices
        self._coerce_fn = coerce
        self.empty_label = empty_label

    @classmethod
    def from_model(
        cls,
        name: str,
        model: Any,
        *,
        label_attr: str = "name",
        value_attr: str = "id",
        order_by: Any = None,
        where: Any = None,
        coerce: Callable[[Any], Any] | None = int,
        **kwargs: Any,
    ) -> "SelectField":
        def provider(s: Session) -> list[Choice]:
            query = s.query(model)
            if where is not None:
                query = query.filter(where)
            if order_by is not None:
                query = query.order_by(order_by)
            return [
                (getattr(row, value_attr), str(getattr(row, label_attr)))
                for row in query.all()
            ]

        return cls(name, choices=provider, coerce=coerce, **kwargs)

    def choices(self, s: Session) -> list[Choice]:
        provider = self._choices
        if callable(provider):
            return list(provider(s))
        return list(provider)

    def _coerce(self, raw: Any) -> Any:
        if raw is None or raw == "":
            return None
        if self._coerce_fn is not None:
            try:
                return self._coerce_fn(raw)
            except (TypeError, ValueError):
                return None
        return raw


class DateTimeField(Field):
    input_type = InputType.DATETIME

    def _coerce(self, raw: Any) -> datetime | None:
        if raw is None or raw == "":
            return None
        try:
            value = datetime.fromisoformat(raw)
        except (TypeError, ValueError):
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value


class HiddenField(Field):
    input_type = InputType.HIDDEN


class JsonAttributesField(Field):
    """Editor for a JSONB ``attributes`` column.

    Renders the dict as typed key/value rows. Supported value types: ``text``,
    ``integer``, ``float``, ``boolean``, ``timestamp``, ``list`` and ``dict``.
    Lists are entered one item per line; dicts as JSON.
    """

    input_type = InputType.ATTRIBUTES

    VALUE_TYPES = (
        (AttrType.TEXT, "Text"),
        (AttrType.INTEGER, "Integer"),
        (AttrType.FLOAT, "Float"),
        (AttrType.BOOLEAN, "Boolean"),
        (AttrType.TIMESTAMP, "Timestamp"),
        (AttrType.LIST, "List"),
        (AttrType.DICT, "Dict"),
    )

    def __init__(
        self,
        name: str = "attributes",
        label: str = "Attributes",
        *,
        readonly: bool = True,
    ) -> None:
        super().__init__(name, label, readonly=readonly)

    @staticmethod
    def type_of(value: Any) -> AttrType:
        if isinstance(value, bool):
            return AttrType.BOOLEAN
        if isinstance(value, int):
            return AttrType.INTEGER
        if isinstance(value, float):
            return AttrType.FLOAT
        if isinstance(value, list):
            return AttrType.LIST
        if isinstance(value, dict):
            return AttrType.DICT
        return AttrType.TEXT

    def rows_from(self, data: Any) -> list[dict[str, Any]]:
        data = data or {}
        result = []
        for key, value in data.items():
            type_ = self.type_of(value)
            result.append({"key": key, "type": type_, "value": self._display(value)})
        return result

    @staticmethod
    def _display(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, list):
            return "\n".join(str(item) for item in value)
        if isinstance(value, dict):
            return json.dumps(value, indent=2, ensure_ascii=False)
        return str(value)

    def parse(self, form: Any, files: Any = None, name: str | None = None) -> dict:
        keys = form.getlist("attr-key")
        types = form.getlist("attr-type")
        values = form.getlist("attr-value")
        result: dict[str, Any] = {}
        for key, type_, value in zip(keys, types, values):
            key = key.strip()
            if not key:
                continue
            result[key] = self._coerce_value(type_, value)
        return result

    @staticmethod
    def _coerce_value(type_: str, raw: str) -> Any:
        raw = raw if raw is not None else ""
        if type_ == AttrType.BOOLEAN:
            return raw.strip().lower() in ("1", "true", "yes", "on")
        if type_ == AttrType.INTEGER:
            try:
                return int(raw)
            except (TypeError, ValueError):
                return 0
        if type_ == AttrType.FLOAT:
            try:
                return float(raw)
            except (TypeError, ValueError):
                return 0.0
        if type_ == AttrType.TIMESTAMP:
            return raw.strip()
        if type_ == AttrType.LIST:
            return [line.strip() for line in raw.splitlines() if line.strip()]
        if type_ == AttrType.DICT:
            try:
                parsed = json.loads(raw) if raw.strip() else {}
            except (TypeError, ValueError):
                parsed = {}
            return parsed if isinstance(parsed, dict) else {}
        return raw

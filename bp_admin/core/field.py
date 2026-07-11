import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Sequence

from sqlalchemy.orm import object_session
from sqlalchemy.orm.session import Session
from web.error import WebError

from .enums import AttrType, InputType
from .utils import default_label, resolve_path

Choice = tuple[Any, str]
ChoiceProvider = Sequence[Choice] | Callable[[Session], Sequence[Choice]]


class Field:
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
        suffix: str | Callable[[Any], Any] | None = None,
        value: str | Callable[[Any], Any] | None = None,
        format: Callable[[Any], Any] | None = None,
        col_class: str | None = None,
    ) -> None:
        self.name = name
        self.label = label if label is not None else default_label(name)
        self.required = required
        self.readonly = readonly
        self.placeholder = placeholder
        self.attrs = attrs or {}
        self.suffix = suffix
        self._value = value
        self._format = format
        self._col_class = col_class

    @property
    def col_class(self) -> str:
        if self._col_class is not None:
            return self._col_class
        if self.input_type in (
            InputType.TEXTAREA,
            InputType.ATTRIBUTES,
            InputType.HTML,
        ):
            return "col-12"
        return "col-12 col-lg-6"

    @property
    def html_input_type(self) -> str:
        if self.input_type is InputType.DATETIME:
            return "datetime-local"
        return self.input_type

    def is_readonly(self, editable: bool | None = None) -> bool:
        return self.readonly if editable is None else not editable

    def suffix_for(self, obj: Any = None) -> Any:
        if callable(self.suffix):
            return self.suffix(obj) if obj is not None else None
        return self.suffix

    #
    # Reading
    #

    def value_from_obj(self, obj: Any) -> Any:
        if callable(self._value):
            raw = self._value(obj)
        elif isinstance(self._value, str):
            raw = resolve_path(obj, self._value)
        else:
            raw = resolve_path(obj, self.name)
        if self._format is not None and raw is not None:
            return self._format(raw)
        return raw

    def form_value(self, obj: Any, form_values: Any) -> Any:
        submitted = form_values.get(self.name)
        if submitted is not None:
            return submitted
        return self.value_from_obj(obj)

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
        if raw != "":
            return raw
        return None


class StringField(Field):
    input_type = InputType.TEXT


class TextAreaField(Field):
    input_type = InputType.TEXTAREA

    def __init__(self, *args: Any, rows: int = 3, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.rows = rows


class HtmlField(Field):
    input_type = InputType.HTML


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

    @property
    def empty_option_label(self) -> str:
        return self.empty_label or "None"

    @property
    def show_empty_option(self) -> bool:
        return self.empty_label is not None or not self.required

    @classmethod
    def from_model(
        cls,
        name: str,
        model: Any,
        *,
        label_attr: str = "name",
        value_attr: str = "id",
        label_fn: Callable[[Any], str] | None = None,
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
            rows = query.all()
            if label_fn is not None:
                return [(getattr(row, value_attr), label_fn(row)) for row in rows]
            return [
                (getattr(row, value_attr), str(getattr(row, label_attr)))
                for row in rows
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


class MultiSelectField(SelectField):
    input_type = InputType.MULTISELECT

    def __init__(
        self,
        name: str,
        label: str | None = None,
        *,
        model: Any = None,
        value_attr: str = "id",
        **kwargs: Any,
    ) -> None:
        super().__init__(name, label, **kwargs)
        self._model = model
        self._value_attr = value_attr

    @classmethod
    def from_model(
        cls,
        name: str,
        model: Any,
        *,
        label_attr: str = "name",
        value_attr: str = "id",
        label_fn: Callable[[Any], str] | None = None,
        order_by: Any = None,
        where: Any = None,
        coerce: Callable[[Any], Any] | None = int,
        **kwargs: Any,
    ) -> "MultiSelectField":
        def provider(s: Session) -> list[Choice]:
            query = s.query(model)
            if where is not None:
                query = query.filter(where)
            if order_by is not None:
                query = query.order_by(order_by)
            rows = query.all()
            if label_fn is not None:
                return [(getattr(row, value_attr), label_fn(row)) for row in rows]
            return [
                (getattr(row, value_attr), str(getattr(row, label_attr)))
                for row in rows
            ]

        return cls(
            name,
            choices=provider,
            coerce=coerce,
            model=model,
            value_attr=value_attr,
            **kwargs,
        )

    def value_from_obj(self, obj: Any) -> list[Any]:
        related = resolve_path(obj, self.name) or []
        return [getattr(item, self._value_attr) for item in related]

    def form_value(self, obj: Any, form_values: Any) -> Any:
        if hasattr(form_values, "getlist"):
            submitted = form_values.getlist(self.name)
            if submitted:
                return submitted
        return self.value_from_obj(obj)

    def parse(self, form: Any, files: Any = None, name: str | None = None) -> list[Any]:
        raw = form.getlist(name or self.name)
        result = []
        for value in raw:
            coerced = self._coerce(value)
            if coerced is not None:
                result.append(coerced)
        return result

    def apply(self, obj: Any, value: Any) -> None:
        if self._model is None:
            return
        session = object_session(obj)
        if session is None:
            return
        ids = value or []
        if ids:
            instances = (
                session.query(self._model)
                .filter(getattr(self._model, self._value_attr).in_(ids))
                .all()
            )
        else:
            instances = []
        setattr(obj, self.name, instances)


class ListTextAreaField(TextAreaField):
    def __init__(self, *args: Any, separator: str = "\n", **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.separator = separator

    def value_from_obj(self, obj: Any) -> str:
        items = resolve_path(obj, self.name) or []
        return self.separator.join(items)

    def parse(self, form: Any, files: Any = None, name: str | None = None) -> list[str]:
        raw = form.get(name or self.name) or ""
        raw = raw.replace("\r\n", "\n")
        chunks = raw.split(self.separator)
        return [chunk.strip() for chunk in chunks if chunk.strip()]


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


class JsonField(Field):
    input_type = InputType.TEXT

    def __init__(self, *args: Any, empty: Any = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._empty = empty

    def value_from_obj(self, obj: Any) -> str:
        value = resolve_path(obj, self.name)
        if value is None:
            return ""
        return json.dumps(value, ensure_ascii=False)

    def _coerce(self, raw: Any) -> Any:
        if raw is None:
            return self._empty
        raw = raw.strip() if isinstance(raw, str) else raw
        if raw == "":
            return self._empty
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            raise WebError(f"Invalid JSON in '{self.label}'.")


class JsonAttributesField(Field):
    input_type = InputType.ATTRIBUTES

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
        if value is None:
            return AttrType.NONE
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
        if value is None:
            return ""
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
            result[key] = self._coerce_value(key, type_, value)
        return result

    @staticmethod
    def _coerce_value(key: str, type_: str, raw: str) -> Any:
        try:
            attr_type = AttrType(type_)
        except ValueError:
            raise WebError(f"Unsupported type '{type_}' for attribute '{key}'.")

        if attr_type is AttrType.NONE:
            return None
        if attr_type is AttrType.BOOLEAN:
            return raw.strip().lower() in ("1", "true", "yes", "on")
        if attr_type is AttrType.INTEGER:
            try:
                return int(raw)
            except (TypeError, ValueError):
                raise WebError(f"Invalid integer for attribute '{key}'.")
        if attr_type is AttrType.FLOAT:
            try:
                return float(raw)
            except (TypeError, ValueError):
                raise WebError(f"Invalid number for attribute '{key}'.")
        if attr_type is AttrType.TIMESTAMP:
            return raw.strip()
        if attr_type is AttrType.LIST:
            return [line.strip() for line in raw.splitlines() if line.strip()]
        if attr_type is AttrType.DICT:
            if not raw.strip():
                return {}
            try:
                parsed = json.loads(raw)
            except (TypeError, ValueError):
                raise WebError(f"Invalid JSON for attribute '{key}'.")
            if not isinstance(parsed, dict):
                raise WebError(f"Attribute '{key}' must be a JSON object.")
            return parsed
        return raw

from typing import Any, Callable

from sqlalchemy.orm.session import Session

from .utils import default_label

FilterOption = tuple[str, str]


class Filter:
    is_divider: bool = False

    def __init__(self, label: str, *, key: str | None = None) -> None:
        self.label = label
        self.key = key

    def options(self, s: Session) -> list[FilterOption]:
        return []

    def apply(self, query: Any, value: str) -> Any:
        return query


class FilterDivider(Filter):
    is_divider = True

    def __init__(self, label: str = "") -> None:
        super().__init__(label)


class BoolFilter(Filter):
    def __init__(
        self,
        column: Any,
        label: str | None = None,
        *,
        key: str | None = None,
    ) -> None:
        if label is None:
            label = default_label(column.key)
        super().__init__(label, key=key)
        self.column = column

    def options(self, s: Session) -> list[FilterOption]:
        return [("1", "Yes"), ("0", "No")]

    def apply(self, query: Any, value: str) -> Any:
        return query.filter(self.column.is_(value == "1"))


class NullFilter(Filter):
    def __init__(
        self,
        column: Any,
        label: str | None = None,
        *,
        key: str | None = None,
    ) -> None:
        if label is None:
            label = default_label(column.key)
        super().__init__(label, key=key)
        self.column = column

    def options(self, s: Session) -> list[FilterOption]:
        return [("0", "Null"), ("1", "Not null")]

    def apply(self, query: Any, value: str) -> Any:
        if value == "0":
            return query.filter(self.column.is_(None))
        return query.filter(self.column.isnot(None))


def _model_options(
    s: Session,
    model: Any,
    label_attr: str,
    order_by: Any,
    label_fn: Callable[[Any], str] | None = None,
) -> list[FilterOption]:
    query = s.query(model)
    if order_by is not None:
        query = query.order_by(order_by)
    elif hasattr(model, "order"):
        query = query.order_by(model.order)
    rows = query.all()
    if label_fn is not None:
        return [(str(row.id), label_fn(row)) for row in rows]
    return [(str(row.id), str(getattr(row, label_attr))) for row in rows]


class FkFilter(Filter):
    def __init__(
        self,
        column: Any,
        model: Any,
        label: str | None = None,
        *,
        label_attr: str = "name",
        label_fn: Callable[[Any], str] | None = None,
        order_by: Any = None,
        coerce: Callable[[str], Any] = int,
        key: str | None = None,
    ) -> None:
        if label is None:
            label = default_label(column.key)
        super().__init__(label, key=key)
        self.column = column
        self.model = model
        self.label_attr = label_attr
        self.label_fn = label_fn
        self.order_by = order_by
        self.coerce = coerce

    def options(self, s: Session) -> list[FilterOption]:
        return _model_options(
            s,
            self.model,
            self.label_attr,
            self.order_by,
            self.label_fn,
        )

    def apply(self, query: Any, value: str) -> Any:
        return query.filter(self.column == self.coerce(value))


class RelationFilter(Filter):
    def __init__(
        self,
        relationship: Any,
        model: Any,
        label: str | None = None,
        *,
        on: Any = None,
        negate: bool = False,
        label_attr: str = "name",
        label_fn: Callable[[Any], str] | None = None,
        order_by: Any = None,
        coerce: Callable[[str], Any] = int,
        key: str | None = None,
    ) -> None:
        if label is None:
            label = default_label(relationship.key)
        super().__init__(label, key=key)
        self.relationship = relationship
        self.model = model
        self.on = on
        self.negate = negate
        self.label_attr = label_attr
        self.label_fn = label_fn
        self.order_by = order_by
        self.coerce = coerce

    @property
    def target(self) -> Any:
        return self.on if self.on is not None else self.model.id

    def options(self, s: Session) -> list[FilterOption]:
        return _model_options(
            s,
            self.model,
            self.label_attr,
            self.order_by,
            self.label_fn,
        )

    def apply(self, query: Any, value: str) -> Any:
        condition = self.relationship.any(self.target == self.coerce(value))
        return query.filter(~condition if self.negate else condition)


class RelationBoolFilter(Filter):
    def __init__(
        self,
        relationship: Any,
        field: Any,
        label: str | None = None,
        *,
        key: str | None = None,
    ) -> None:
        if label is None:
            label = default_label(relationship.key)
        super().__init__(label, key=key)
        self.relationship = relationship
        self.field = field

    def options(self, s: Session) -> list[FilterOption]:
        return [("1", "Yes"), ("0", "No")]

    def apply(self, query: Any, value: str) -> Any:
        condition = self.relationship.any(self.field)
        return query.filter(condition if value == "1" else ~condition)

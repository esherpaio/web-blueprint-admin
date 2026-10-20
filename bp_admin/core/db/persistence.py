from typing import Any, Iterable

from sqlalchemy import func
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm.session import Session

from ..column import Column, row_input_name
from ..field import Field


def parse_ids(model: Any, values: Iterable[Any]) -> list[Any]:
    python_type = sa_inspect(model).columns["id"].type.python_type
    return [python_type(value) for value in values]


def next_order(query: Any, order_column: Any) -> int:
    current = query.with_entities(func.max(order_column)).order_by(None).scalar()
    return (current or 0) + 1


def apply_fields(
    obj: Any,
    fields: Iterable[Field],
    form: Any,
    files: Any = None,
    *,
    respect_readonly: bool = True,
) -> None:
    for field in fields:
        if respect_readonly and field.readonly:
            continue
        field.apply(obj, field.parse(form, files))


def apply_bulk_fields(
    s: Session,
    model: Any,
    columns: Iterable[Column],
    form: Any,
    *,
    base_query: Any = None,
    order_field: str | None = None,
) -> int:
    editable = [c for c in columns if c.editable]

    raw_ids = form.getlist("row-id")
    if not raw_ids or (not editable and order_field is None):
        return 0

    input_ids = dict(zip(parse_ids(model, raw_ids), raw_ids))
    query = base_query if base_query is not None else s.query(model)
    rows = query.filter(model.id.in_(input_ids.keys())).all()
    for row in rows:
        raw_id = input_ids[row.id]
        for column in editable:
            value = column.field.parse(form, name=column.input_name(raw_id))
            column.field.apply(row, value)
        if order_field is not None:
            try:
                order = int(form.get(row_input_name(raw_id, order_field)))
                setattr(row, order_field, order)
            except (TypeError, ValueError):
                pass
    return len(rows)


def delete_objects(
    s: Session,
    model: Any,
    ids: Iterable[Any],
    *,
    soft_delete: bool,
    base_query: Any = None,
) -> int:
    ids = [i for i in ids if i not in (None, "")]
    if not ids:
        return 0
    ids = parse_ids(model, ids)
    query = base_query if base_query is not None else s.query(model)
    rows = query.filter(model.id.in_(ids)).all()
    for row in rows:
        if soft_delete:
            row.is_deleted = True
        else:
            s.delete(row)
    return len(rows)

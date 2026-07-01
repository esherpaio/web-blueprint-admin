from typing import Any, Iterable

from sqlalchemy.orm.session import Session

from ..column import Column, row_input_name
from ..field import Field


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
    row_ids = form.getlist("row-id")
    if not row_ids or (not editable and order_field is None):
        return 0
    query = base_query if base_query is not None else s.query(model)
    rows = {str(row.id): row for row in query.filter(model.id.in_(row_ids)).all()}
    for row_id in row_ids:
        row = rows.get(str(row_id))
        if row is None:
            continue
        for column in editable:
            value = column.field.parse(form, name=row_input_name(row_id, column.name))
            column.field.apply(row, value)
        if order_field is not None:
            raw = form.get(row_input_name(row_id, order_field))
            if raw not in (None, ""):
                try:
                    setattr(row, order_field, int(raw))
                except (TypeError, ValueError):
                    pass
    return len(row_ids)


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
    query = base_query if base_query is not None else s.query(model)
    rows = query.filter(model.id.in_(ids)).all()
    for row in rows:
        if soft_delete:
            row.is_deleted = True
        else:
            s.delete(row)
    return len(rows)

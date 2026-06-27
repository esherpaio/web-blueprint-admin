"""Shared persistence helpers for the declarative admin engine."""

from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy.orm.session import Session

from .column import Column
from .field import Field


def supports_soft_delete(model: Any) -> bool:
    return hasattr(model, "is_deleted")


def resolve_choices(s: Session, fields: Iterable[Field]) -> dict[str, list]:
    choices: dict[str, list] = {}
    for field in fields:
        if field.input_type == "select":
            choices[field.name] = field.choices(s)
    return choices


def apply_fields(
    obj: Any,
    fields: Iterable[Field],
    form: Any,
    files: Any = None,
) -> None:
    for field in fields:
        if field.readonly:
            continue
        field.apply(obj, field.parse(form, files))


def apply_bulk_edits(
    s: Session, model: Any, columns: Iterable[Column], form: Any
) -> int:
    editable = [c for c in columns if c.editable]
    row_ids = form.getlist("row-id")
    if not editable or not row_ids:
        return 0
    rows = {
        str(row.id): row for row in s.query(model).filter(model.id.in_(row_ids)).all()
    }
    for row_id in row_ids:
        row = rows.get(str(row_id))
        if row is None:
            continue
        for column in editable:
            value = column.field.parse(form, name=f"rows-{row_id}-{column.name}")
            column.field.apply(row, value)
    return len(row_ids)


def delete_objects(
    s: Session,
    model: Any,
    ids: Iterable[Any],
    *,
    soft_delete: bool,
) -> int:
    ids = [i for i in ids if i not in (None, "")]
    if not ids:
        return 0
    rows = s.query(model).filter(model.id.in_(ids)).all()
    for row in rows:
        if soft_delete:
            row.is_deleted = True
        else:
            s.delete(row)
    return len(rows)

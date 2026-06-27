"""Shared persistence helpers for the declarative admin engine."""

from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy.orm.session import Session

from .column import Column
from .field import Field


def supports_soft_delete(model: Any) -> bool:
    return hasattr(model, "is_deleted")


def resolve_choices(s: Session, fields: Iterable[Field]) -> dict[str, list]:
    """Resolve options for every select field, keyed by field name.

    Done eagerly inside the request's session so templates never touch the DB
    and we avoid mutating shared field instances across threads.
    """
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
    """Set each field's parsed value on ``obj``."""
    for field in fields:
        if field.readonly:
            continue
        setattr(obj, field.name, field.parse(form, files))


def apply_bulk_edits(
    s: Session, model: Any, columns: Iterable[Column], form: Any
) -> int:
    """Apply inline edits for all submitted ``rows-<id>-<col>`` inputs.

    Returns the number of rows that were inspected. Only editable columns are
    written; SQLAlchemy flushes only the rows whose values actually changed.
    """
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
            setattr(row, column.name, value)
    return len(row_ids)


def delete_objects(
    s: Session,
    model: Any,
    ids: Iterable[Any],
    *,
    soft_delete: bool,
) -> int:
    """Soft- or hard-delete the rows with the given ids."""
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

"""Detail-page tabs for the declarative admin engine.

Detail/edit pages are composed from declarative tabs so a page can mix regular
forms, editable child tables and fully custom layouts (e.g. a media gallery):

* :class:`FormTab` edits fields on the object itself.
* :class:`InlineTableTab` manages child rows related by a foreign key.
* :class:`MediaTab` uploads files to the CDN and edits the resulting gallery.
* :class:`TemplateTab` renders an author-supplied template for custom content.
"""

import os
import re
from typing import Any, Callable

from sqlalchemy.orm.session import Session
from web import cdn
from web.database.model import File, FileTypeId
from web.setup import config
from werkzeug.utils import secure_filename

from .column import Column, row_input_name
from .enums import Op
from .field import Field
from .util import (
    apply_bulk_edits,
    apply_fields,
    delete_objects,
    resolve_choices,
    supports_soft_delete,
)


def _slug(label: str) -> str:
    return label.strip().lower().replace(" ", "-")


class Tab:
    template = "admin/_engine/_tab_form.html"

    def __init__(self, label: str, key: str | None = None) -> None:
        self.label = label
        self.key = key or _slug(label)

    @property
    def form_id(self) -> str:
        return f"form-{self.key}"

    def context(self, view: Any, s: Session, obj: Any) -> dict[str, Any]:
        return {}

    def handle_post(
        self, view: Any, s: Session, obj: Any, form: Any, files: Any
    ) -> None:
        pass


class FormTab(Tab):
    """Edit a set of fields directly on the object."""

    template = "admin/_engine/_tab_form.html"

    def __init__(
        self,
        label: str = "General",
        fields: list[Field] | None = None,
        *,
        key: str = "general",
    ) -> None:
        super().__init__(label, key)
        self.fields = fields or []

    @property
    def has_editable(self) -> bool:
        return any(not field.readonly for field in self.fields)

    def context(self, view: Any, s: Session, obj: Any) -> dict[str, Any]:
        return {"fields": self.fields, "choices": resolve_choices(s, self.fields)}

    def handle_post(
        self, view: Any, s: Session, obj: Any, form: Any, files: Any
    ) -> None:
        apply_fields(obj, self.fields, form, files)
        s.flush()
        view.after_write(s, obj)


class InlineTableTab(Tab):
    """A bulk-editable table of child rows related to the parent by ``fk``."""

    template = "admin/_engine/_tab_inline.html"

    def __init__(
        self,
        label: str,
        model: Any,
        fk: str,
        columns: list[Column],
        *,
        create_fields: list[Field] | None = None,
        order_by: Any = None,
        query: Callable[[Session, Any], Any] | None = None,
        soft_delete: bool | None = None,
        can_create: bool = True,
        can_delete: bool = True,
        reorderable: bool = False,
        order_field: str = "order",
        key: str | None = None,
    ) -> None:
        super().__init__(label, key)
        self.model = model
        self.fk = fk
        self.columns = columns
        self.create_fields = create_fields or []
        self.order_by = order_by
        self._query = query
        self._soft_delete = soft_delete
        self.can_create = can_create
        self.can_delete = can_delete
        self.reorderable = reorderable
        self.order_field = order_field

    @property
    def soft_delete(self) -> bool:
        if self._soft_delete is not None:
            return self._soft_delete
        return supports_soft_delete(self.model)

    @property
    def add_modal_id(self) -> str:
        return f"modal-add-{self.key}"

    @property
    def has_editable(self) -> bool:
        return any(column.editable for column in self.columns)

    @property
    def show_add(self) -> bool:
        return self.can_create and bool(self.create_fields)

    @property
    def show_save(self) -> bool:
        return self.reorderable or self.has_editable

    @property
    def show_toolbar(self) -> bool:
        return self.show_add or self.show_save or self.can_delete

    def order_input_name(self, row_id: Any) -> str:
        return row_input_name(row_id, self.order_field)

    def base_query(self, s: Session, obj: Any) -> Any:
        if self._query is not None:
            return self._query(s, obj)
        query = s.query(self.model).filter(getattr(self.model, self.fk) == obj.id)
        if supports_soft_delete(self.model):
            query = query.filter(self.model.is_deleted.is_(False))
        if self.order_by is not None:
            query = query.order_by(self.order_by)
        return query

    def context(self, view: Any, s: Session, obj: Any) -> dict[str, Any]:
        rows = self.base_query(s, obj).all()
        fields = [c.field for c in self.columns] + self.create_fields
        actions = [a for a in view.actions if a.tab == self.key and a.is_visible(obj)]
        return {
            "tab": self,
            "rows": rows,
            "columns": self.columns,
            "create_fields": self.create_fields,
            "choices": resolve_choices(s, fields),
            "actions": actions,
        }

    def handle_post(
        self, view: Any, s: Session, obj: Any, form: Any, files: Any
    ) -> None:
        op = form.get("_op")
        if op == Op.ADD and self.can_create:
            child = self.model()
            setattr(child, self.fk, obj.id)
            apply_fields(child, self.create_fields, form, files, respect_readonly=False)
            s.add(child)
            s.flush()
        elif op == Op.DELETE and self.can_delete:
            delete_objects(
                s,
                self.model,
                form.getlist("select"),
                soft_delete=self.soft_delete,
                base_query=self.base_query(s, obj),
            )
        else:
            apply_bulk_edits(
                s,
                self.model,
                self.columns,
                form,
                base_query=self.base_query(s, obj),
                order_field=self.order_field if self.reorderable else None,
            )
        view.after_write(s, obj)


class MediaTab(Tab):
    """Upload files to the CDN and manage the resulting gallery.

    Each row links a parent (via ``fk``) to a :class:`File` through ``file_rel``.
    Uploaded files are stored under ``path_prefix(parent)`` and typed from their
    extension; rows are reorderable and carry an editable file description.
    """

    template = "admin/_engine/_tab_media.html"

    def __init__(
        self,
        label: str,
        model: Any,
        fk: str,
        *,
        path_prefix: Callable[[Any], tuple[str, ...]],
        file_rel: str = "file_",
        order_field: str = "order",
        can_delete: bool = True,
        key: str | None = None,
    ) -> None:
        super().__init__(label, key)
        self.model = model
        self.fk = fk
        self.path_prefix = path_prefix
        self.file_rel = file_rel
        self.order_field = order_field
        self.can_delete = can_delete

    @property
    def add_modal_id(self) -> str:
        return f"modal-add-{self.key}"

    def order_input_name(self, row_id: Any) -> str:
        return row_input_name(row_id, self.order_field)

    def description_input_name(self, row_id: Any) -> str:
        return row_input_name(row_id, "description")

    def base_query(self, s: Session, obj: Any) -> Any:
        return (
            s.query(self.model)
            .filter(getattr(self.model, self.fk) == obj.id)
            .order_by(getattr(self.model, self.order_field), self.model.id)
        )

    def context(self, view: Any, s: Session, obj: Any) -> dict[str, Any]:
        return {"tab": self, "rows": self.base_query(s, obj).all()}

    def handle_post(
        self, view: Any, s: Session, obj: Any, form: Any, files: Any
    ) -> None:
        op = form.get("_op")
        if op == Op.ADD:
            self._upload(s, obj, files)
        elif op == Op.DELETE and self.can_delete:
            self._delete(s, obj, form.getlist("select"))
        else:
            self._save(s, obj, form)
        view.after_write(s, obj)

    def _upload(self, s: Session, obj: Any, files: Any) -> None:
        prefix = self.path_prefix(obj)
        sequence = self._last_sequence(s, obj)
        for upload in files.getlist("file"):
            if not upload.filename:
                continue
            extension = os.path.splitext(upload.filename)[1].lstrip(".").lower()
            type_id = self._type_for(extension)
            if type_id is None:
                continue
            sequence += 1
            if config.CDN_AUTO_NAMING:
                name = f"{prefix[-1]}-{sequence}"
            else:
                name = secure_filename(os.path.splitext(upload.filename)[0])
            path = os.path.join(*prefix, f"{name}.{extension}")
            cdn.upload(upload, path)
            file_ = File(path=path, type_id=type_id)
            s.add(file_)
            s.flush()
            child = self.model()
            setattr(child, self.fk, obj.id)
            setattr(child, f"{self.file_rel}_id", file_.id)
            s.add(child)
            s.flush()

    def _save(self, s: Session, obj: Any, form: Any) -> None:
        rows = {str(r.id): r for r in self.base_query(s, obj).all()}
        for row_id in form.getlist("row-id"):
            row = rows.get(str(row_id))
            if row is None:
                continue
            order = form.get(self.order_input_name(row_id))
            if order not in (None, ""):
                try:
                    setattr(row, self.order_field, int(order))
                except (TypeError, ValueError):
                    pass
            file_ = getattr(row, self.file_rel)
            if file_ is not None:
                file_.description = (
                    form.get(self.description_input_name(row_id)) or None
                )

    def _delete(self, s: Session, obj: Any, ids: list[Any]) -> None:
        rows = self.base_query(s, obj).filter(self.model.id.in_(ids)).all()
        for row in rows:
            file_ = getattr(row, self.file_rel)
            if file_ is not None:
                cdn.delete(file_.path)
                s.delete(file_)
            s.delete(row)

    def _last_sequence(self, s: Session, obj: Any) -> int:
        if not config.CDN_AUTO_NAMING:
            return 0
        last = (
            self.base_query(s, obj)
            .order_by(None)
            .order_by(self.model.id.desc())
            .first()
        )
        file_ = getattr(last, self.file_rel, None) if last else None
        match = re.search(r"(\d+)\.\w+$", file_.path) if file_ else None
        return int(match.group(1)) if match else 0

    @staticmethod
    def _type_for(extension: str) -> int | None:
        if extension in config.CDN_IMAGE_EXTS:
            return FileTypeId.IMAGE
        if extension in config.CDN_VIDEO_EXTS:
            return FileTypeId.VIDEO
        return None


class TemplateTab(Tab):
    """Render an author-supplied template for fully custom tab content."""

    template = "admin/_engine/_tab_template.html"

    def __init__(
        self,
        label: str,
        template: str,
        *,
        key: str | None = None,
        context: Callable[[Session, Any], dict[str, Any]] | None = None,
        handler: Callable[[Session, Any, Any, Any], None] | None = None,
    ) -> None:
        super().__init__(label, key)
        self.user_template = template
        self._context = context
        self._handler = handler

    def context(self, view: Any, s: Session, obj: Any) -> dict[str, Any]:
        extra = self._context(s, obj) if self._context is not None else {}
        return {"user_template": self.user_template, **extra}

    def handle_post(
        self, view: Any, s: Session, obj: Any, form: Any, files: Any
    ) -> None:
        if self._handler is not None:
            self._handler(s, obj, form, files)
        view.after_write(s, obj)

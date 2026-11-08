import os
import re
import secrets
from dataclasses import asdict
from typing import Any, Callable

from flask import abort
from sqlalchemy.orm.session import Session
from web.cdn import Client, cdn_url
from web.database.model import File, FileTypeId
from web.error import WebError
from web.setup import config
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from ..content import BLOCK_TYPES, Content, FileRef, parse_content, render_content
from .column import Column, row_input_name
from .db import (
    apply_bulk_fields,
    apply_fields,
    delete_objects,
    next_order,
    parse_ids,
    resolve_choices,
    supports_soft_delete,
)
from .enums import ActionScope, Op
from .field import Field


class Tab:
    template = "admin/_engine/_tab_form.html"

    def __init__(self, label: str, key: str | None = None) -> None:
        self.label = label
        self.key = key or self.slugify(label)

    @staticmethod
    def slugify(label: str) -> str:
        return label.strip().lower().replace(" ", "-")

    @property
    def form_id(self) -> str:
        return f"form-{self.key}"

    def context(self, view: Any, s: Session, obj: Any) -> dict[str, Any]:
        return {}

    def handle_post(
        self,
        view: Any,
        s: Session,
        obj: Any,
        form: Any,
        files: Any,
    ) -> None:
        pass


class FormSection:
    def __init__(
        self,
        label: str,
        fields: list[Field],
        *,
        visible: Callable[[Any], bool] | None = None,
    ) -> None:
        self.label = label
        self.fields = fields
        self._visible = visible

    def is_visible(self, obj: Any) -> bool:
        return self._visible(obj) if self._visible is not None else True


class FormTab(Tab):
    template = "admin/_engine/_tab_form.html"

    def __init__(
        self,
        label: str = "General",
        fields: list[Field] | None = None,
        *,
        key: str = "general",
        sections: list[FormSection] | None = None,
    ) -> None:
        super().__init__(label, key)
        if fields is not None and sections is not None:
            raise ValueError("Use either fields or sections, not both.")
        self.sections = sections or []
        self.fields = (
            [field for section in self.sections for field in section.fields]
            if self.sections
            else fields or []
        )

    @property
    def has_editable(self) -> bool:
        return any(not field.readonly for field in self.fields)

    def visible_sections(self, obj: Any) -> list[FormSection]:
        return [section for section in self.sections if section.is_visible(obj)]

    def visible_fields(self, obj: Any) -> list[Field]:
        if not self.sections:
            return self.fields
        return [
            field for section in self.visible_sections(obj) for field in section.fields
        ]

    def context(self, view: Any, s: Session, obj: Any) -> dict[str, Any]:
        fields = self.visible_fields(obj)
        return {
            "fields": fields,
            "sections": self.visible_sections(obj),
            "choices": resolve_choices(s, fields),
            "has_editable": any(not field.readonly for field in fields),
        }

    def handle_post(
        self,
        view: Any,
        s: Session,
        obj: Any,
        form: Any,
        files: Any,
    ) -> None:
        apply_fields(obj, self.visible_fields(obj), form, files)
        s.flush()
        view.after_write(s, obj)


class InlineTableTab(Tab):
    template = "admin/_engine/_tab_inline.html"

    def __init__(
        self,
        name: str,
        model: Any,
        fk: str,
        columns: list[Column],
        *,
        name_plural: str | None = None,
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
        self.name = name
        self.name_plural = name_plural or f"{name}s"
        super().__init__(self.name_plural, key)
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
    def add_title(self) -> str:
        return f"Add {self.name}"

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
        actions = [
            a
            for a in view.actions
            if a.scope is ActionScope.DETAIL and a.tab == self.key and a.is_visible(obj)
        ]
        return {
            "tab": self,
            "rows": rows,
            "columns": self.columns,
            "create_fields": self.create_fields,
            "choices": resolve_choices(s, fields),
            "actions": actions,
        }

    def handle_post(
        self,
        view: Any,
        s: Session,
        obj: Any,
        form: Any,
        files: Any,
    ) -> None:
        try:
            op = Op(form.get("_op", ""))
        except ValueError:
            abort(400)
        if op is Op.ADD and self.can_create:
            child = self.model()
            s.add(child)
            with s.no_autoflush:
                setattr(child, self.fk, obj.id)
                apply_fields(
                    child, self.create_fields, form, files, respect_readonly=False
                )
                if self.reorderable and getattr(child, self.order_field, None) is None:
                    order_column = getattr(self.model, self.order_field)
                    order = next_order(self.base_query(s, obj), order_column)
                    setattr(child, self.order_field, order)
            s.flush()
        elif op is Op.DELETE and self.can_delete:
            delete_objects(
                s,
                self.model,
                form.getlist("select"),
                soft_delete=self.soft_delete,
                base_query=self.base_query(s, obj),
            )
        elif op is Op.SAVE:
            apply_bulk_fields(
                s,
                self.model,
                self.columns,
                form,
                base_query=self.base_query(s, obj),
                order_field=self.order_field if self.reorderable else None,
            )
        else:
            abort(400)
        view.after_write(s, obj)


class MediaTab(Tab):
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
        self,
        view: Any,
        s: Session,
        obj: Any,
        form: Any,
        files: Any,
    ) -> None:
        try:
            op = Op(form.get("_op", ""))
        except ValueError:
            abort(400)
        if op is Op.ADD:
            self._upload(s, obj, files)
        elif op is Op.DELETE and self.can_delete:
            self._delete(s, obj, form.getlist("select"))
        elif op is Op.SAVE:
            self._save(s, obj, form)
        else:
            abort(400)
        view.after_write(s, obj)

    def _upload(self, s: Session, obj: Any, files: Any) -> None:
        prefix = self.path_prefix(obj)
        sequence = self._last_sequence(s, obj)
        with Client.connect() as c:
            for upload in files.getlist("file"):
                if not upload.filename:
                    continue
                extension = os.path.splitext(upload.filename)[1].lstrip(".").lower()
                type_id = _file_type(extension, (FileTypeId.IMAGE, FileTypeId.VIDEO))
                if type_id is None:
                    continue
                sequence += 1
                if config.CDN_AUTO_NAMING:
                    name = f"{prefix[-1]}-{sequence}"
                else:
                    name = secure_filename(os.path.splitext(upload.filename)[0])
                path = os.path.join(*prefix, f"{name}.{extension}")
                c.upload(upload, path)
                file_ = File(path=path, type_id=type_id)
                s.add(file_)
                s.flush()
                child = self.model()
                setattr(child, self.fk, obj.id)
                setattr(child, self.file_rel, file_)
                s.add(child)
                s.flush()

    def _save(self, s: Session, obj: Any, form: Any) -> None:
        raw_ids = form.getlist("row-id")
        if not raw_ids:
            return
        input_ids = dict(zip(parse_ids(self.model, raw_ids), raw_ids))
        rows = self.base_query(s, obj).filter(self.model.id.in_(input_ids.keys())).all()
        for row in rows:
            raw_id = input_ids[row.id]
            try:
                order = int(form.get(self.order_input_name(raw_id)))
                setattr(row, self.order_field, order)
            except (TypeError, ValueError):
                pass
            file_ = getattr(row, self.file_rel)
            if file_ is not None:
                file_.description = (
                    form.get(self.description_input_name(raw_id)) or None
                )

    def _delete(self, s: Session, obj: Any, ids: list[Any]) -> None:
        ids = parse_ids(self.model, ids)
        if not ids:
            return
        rows = self.base_query(s, obj).filter(self.model.id.in_(ids)).all()
        _delete_medias(s, rows, self.file_rel)

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


class ContentTab(Tab):
    """Editor.js tab; owns its media rows, so don't share the model with a MediaTab."""

    template = "admin/_engine/_tab_content.html"

    def __init__(
        self,
        label: str,
        model: Any = None,
        fk: str | None = None,
        *,
        template_dir: str,
        path_prefix: Callable[[Any], tuple[str, ...]] | None = None,
        block_types: tuple[str, ...] = tuple(BLOCK_TYPES),
        preview_url: Callable[[Any], str] | None = None,
        key: str | None = None,
    ) -> None:
        super().__init__(label, key)
        self.model = model
        self.fk = fk
        self.template_dir = template_dir
        self.path_prefix = path_prefix
        self.block_types = block_types
        self.preview_url = preview_url

    def context(self, view: Any, s: Session, obj: Any) -> dict[str, Any]:
        upload_url = None
        if self.model is not None:
            upload_url = view.url("tab_upload", id_=obj.id, tab_key=self.key)
        return {
            "editor": {
                "data": obj.content or {"blocks": []},
                "tools": self.block_types,
                "uploadUrl": upload_url,
            },
            "preview_url": self.preview_url(obj) if self.preview_url else None,
        }

    def handle_post(
        self,
        view: Any,
        s: Session,
        obj: Any,
        form: Any,
        files: Any,
    ) -> None:
        try:
            content = parse_content(
                form.get("content", ""),
                block_types=self.block_types,
            )
        except ValueError as error:
            raise WebError("Invalid content") from error
        self._sync_files(s, obj, content)
        obj.content = asdict(content)
        obj.html = render_content(content, self.template_dir)
        s.flush()
        view.after_write(s, obj)

    def upload(self, s: Session, obj: Any, upload: FileStorage) -> FileRef:
        stem, extension = os.path.splitext(upload.filename or "")
        extension = extension.lstrip(".").lower()
        type_id = _file_type(extension, (FileTypeId.IMAGE, FileTypeId.DOCUMENT))
        if type_id is None:
            raise WebError(f"Files of type .{extension} are not allowed")
        name = f"{secure_filename(stem) or 'file'}-{secrets.token_hex(4)}.{extension}"
        path = os.path.join(*self.path_prefix(obj), name)
        with Client.connect() as c:
            c.upload(upload, path)
        file_ = File(path=path, type_id=type_id)
        media = self.model(file_=file_)
        setattr(media, self.fk, obj.id)
        s.add(media)
        s.flush()
        return FileRef(
            id=file_.id,
            url=cdn_url(file_.path),
            path=file_.path,
            name=upload.filename,
            extension=extension,
        )

    def _sync_files(self, s: Session, obj: Any, content: Content) -> None:
        if self.model is None:
            return
        medias = {
            media.file_id: media
            for media in s.query(self.model).filter(
                getattr(self.model, self.fk) == obj.id
            )
        }
        # unique ids, in the order they appear in the content
        file_ids = list(dict.fromkeys(ref.id for ref in content.files))
        if not set(file_ids) <= medias.keys():
            raise WebError("Content refers to files that are not linked to it")
        for ref in content.files:
            ref.path = medias[ref.id].file_.path
        for order, file_id in enumerate(file_ids, start=1):
            medias.pop(file_id).order = order
        _delete_medias(s, list(medias.values()))


def _file_type(extension: str, type_ids: tuple[FileTypeId, ...]) -> FileTypeId | None:
    extensions = {
        FileTypeId.IMAGE: config.CDN_IMAGE_EXTS,
        FileTypeId.VIDEO: config.CDN_VIDEO_EXTS,
        FileTypeId.DOCUMENT: config.CDN_DOCUMENT_EXTS,
    }
    return next((id_ for id_ in type_ids if extension in extensions[id_]), None)


def _delete_medias(s: Session, rows: list[Any], file_rel: str = "file_") -> None:
    if not rows:
        return
    with Client.connect() as c:
        for row in rows:
            file_ = getattr(row, file_rel)
            if file_ is not None:
                c.delete(file_.path)
                s.delete(file_)
            s.delete(row)

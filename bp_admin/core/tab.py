"""Detail-page tabs for the declarative admin engine.

Detail/edit pages are composed from declarative tabs so a page can mix regular
forms, editable child tables and fully custom layouts (e.g. a media gallery):

* :class:`FormTab` edits fields on the object itself.
* :class:`InlineTableTab` manages child rows related by a foreign key.
* :class:`TemplateTab` renders an author-supplied template for custom content.
"""

from typing import Any, Callable

from sqlalchemy.orm.session import Session

from .column import Column
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
        return {
            "tab": self,
            "rows": rows,
            "columns": self.columns,
            "create_fields": self.create_fields,
            "choices": resolve_choices(s, fields),
        }

    def handle_post(
        self, view: Any, s: Session, obj: Any, form: Any, files: Any
    ) -> None:
        op = form.get("_op")
        if op == "add" and self.can_create:
            child = self.model()
            setattr(child, self.fk, obj.id)
            apply_fields(child, self.create_fields, form, files)
            s.add(child)
            s.flush()
        elif op == "delete" and self.can_delete:
            delete_objects(
                s, self.model, form.getlist("select"), soft_delete=self.soft_delete
            )
        else:
            apply_bulk_edits(
                s,
                self.model,
                self.columns,
                form,
                order_field=self.order_field if self.reorderable else None,
            )
        view.after_write(s, obj)


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

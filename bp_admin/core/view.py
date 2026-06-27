"""The declarative :class:`ModelView` — the heart of the admin engine.

Subclass it per model to describe a list page (optionally bulk-editable), a
modal create form, a tabbed detail/edit page and custom actions. The engine
turns that description into routes, queries and Bootstrap templates.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm.session import Session

from .action import Action
from .column import Column
from .field import Field
from .tab import Tab
from .util import apply_fields, supports_soft_delete


class Filter:
    """A simple equality filter rendered as a ``<select>`` on the list page."""

    def __init__(
        self,
        name: str,
        label: str | None = None,
        *,
        choices: Any = (),
        coerce: Any = int,
        empty_label: str = "All",
    ) -> None:
        self.name = name
        self.label = label if label is not None else name.replace("_", " ").capitalize()
        self._choices = choices
        self.coerce = coerce
        self.empty_label = empty_label

    def choices(self, s: Session) -> list:
        if callable(self._choices):
            return list(self._choices(s))
        return list(self._choices)


class ModelView:
    # Identity
    model: Any = None
    name: str = ""
    name_plural: str | None = None
    endpoint: str | None = None

    # Menu placement
    icon: str | None = None
    menu_group: str | None = None
    menu_section: str = "main"
    order: int = 100

    # List page
    columns: list[Column] = []
    searchable: list[str] = []
    filters: list[Filter] = []
    page_size: int = 40
    order_by: Any = None

    # Create (modal)
    create_fields: list[Field] = []

    # Detail/edit page
    tabs: list[Tab] = []
    actions: list[Action] = []

    # Capabilities
    can_create: bool = True
    can_delete: bool = True
    can_edit: bool = True
    _soft_delete: bool | None = None

    def __init__(self) -> None:
        if not self.name:
            self.name = type(self).__name__.replace("View", "")
        if self.name_plural is None:
            self.name_plural = self.name + "s"
        if self.endpoint is None:
            self.endpoint = self.name_plural.lower().replace(" ", "_")

    #
    # Derived properties
    #

    @property
    def slug(self) -> str:
        assert self.endpoint is not None
        return self.endpoint

    @property
    def soft_delete(self) -> bool:
        if self._soft_delete is not None:
            return self._soft_delete
        return supports_soft_delete(self.model)

    @property
    def has_detail(self) -> bool:
        return self.can_edit and bool(self.tabs)

    @property
    def has_bulk_edit(self) -> bool:
        return any(column.editable for column in self.columns)

    def tab_by_key(self, key: str) -> Tab | None:
        for tab in self.tabs:
            if tab.key == key:
                return tab
        return None

    def action_by_name(self, name: str) -> Action | None:
        for action in self.actions:
            if action.name == name:
                return action
        return None

    #
    # Querying
    #

    def get_query(self, s: Session) -> Any:
        query = s.query(self.model)
        if supports_soft_delete(self.model):
            query = query.filter(self.model.is_deleted.is_(False))
        return query

    def apply_search(self, query: Any, search: str) -> Any:
        if not search or not self.searchable:
            return query
        conditions = [
            getattr(self.model, name).ilike(f"%{search}%") for name in self.searchable
        ]
        return query.filter(or_(*conditions))

    def apply_filters(self, query: Any, values: dict[str, Any]) -> Any:
        for filter_ in self.filters:
            raw = values.get(filter_.name)
            if raw in (None, ""):
                continue
            try:
                value = filter_.coerce(raw)
            except (TypeError, ValueError):
                continue
            query = query.filter(getattr(self.model, filter_.name) == value)
        return query

    def apply_order(self, query: Any) -> Any:
        if self.order_by is not None:
            if isinstance(self.order_by, (list, tuple)):
                return query.order_by(*self.order_by)
            return query.order_by(self.order_by)
        return query.order_by(self.model.id.desc())

    #
    # Operations
    #

    def get_object(self, s: Session, id_: Any) -> Any:
        return s.query(self.model).filter(self.model.id == id_).first()

    def create(self, s: Session, form: Any, files: Any) -> Any:
        obj = self.model()
        apply_fields(obj, self.create_fields, form, files)
        s.add(obj)
        s.flush()
        self.after_write(s, obj)
        return obj

    #
    # Hooks
    #

    def after_write(self, s: Session, obj: Any = None) -> None:
        pass

from typing import Any

import requests
from flask import render_template
from sqlalchemy import or_
from sqlalchemy.orm.session import Session
from web.app.urls import url_for
from web.database.model import AppSettings
from web.utils.markdown import Markdown

from .action import Action
from .column import Column, Link, row_input_name
from .db import apply_fields, supports_soft_delete
from .enums import MenuSection
from .field import Field
from .menu import NavSource
from .tab import Tab


class ModelView:
    # Identity
    model: Any = None
    name: str = ""
    name_plural: str | None = None
    endpoint: str | None = None

    # Menu placement
    icon: str | None = None
    menu_group: str | None = None
    menu_section: MenuSection = MenuSection.MAIN
    order: int = 100
    is_home: bool = False

    # List page
    columns: list[Column] = []
    header_links: list[Link] = []
    searchable: list[str] = []
    page_size: int = 40
    order_by: Any = None
    reorderable: bool = False
    order_field: str = "order"

    # Create modal
    create_fields: list[Field] = []

    # Detail page
    tabs: list[Tab] = []

    # Action buttons
    actions: list[Action] = []

    # Capabilities
    can_create: bool = False
    can_delete: bool = False
    can_edit: bool = False
    singleton: bool = False
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
    def route(self) -> str:
        return f"admin.{self.endpoint}"

    @property
    def nav_source(self) -> NavSource | None:
        if self.menu_section is MenuSection.HIDDEN:
            return None
        return NavSource(
            section=self.menu_section,
            label=self.name_plural or self.name,
            endpoint=self.route,
            match=self.route,
            order=self.order,
            icon=self.icon,
            group=self.menu_group,
        )

    def url(self, suffix: str = "", **values: Any) -> str:
        endpoint = self.route if not suffix else f"{self.route}_{suffix}"
        return url_for(endpoint, **values)

    def order_input_name(self, row_id: Any) -> str:
        return row_input_name(row_id, self.order_field)

    def title(self, obj: Any) -> str:
        return getattr(obj, "name", None) or f"{self.name} #{obj.id}"

    @property
    def create_title(self) -> str:
        return f"Add {self.name.lower()}"

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
        return self.reorderable or any(column.editable for column in self.columns)

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
        apply_fields(obj, self.create_fields, form, files, respect_readonly=False)
        s.add(obj)
        s.flush()
        self.after_write(s, obj)
        return obj

    #
    # Hooks
    #

    def after_write(self, s: Session, obj: Any = None) -> None:
        pass


class SingletonView(ModelView):
    singleton = True
    can_edit = True


class CachedModelView(ModelView):
    def after_write(self, s: Session, obj: Any = None) -> None:
        settings = s.query(AppSettings).first()
        if settings is not None:
            settings.cached_at = None


class MarkdownView:
    endpoint: str = ""
    label: str = ""
    url: str = ""
    icon: str | None = None
    order: int = 100
    menu_section: MenuSection = MenuSection.BOTTOM
    menu_group: str | None = None

    @property
    def route(self) -> str:
        return f"admin.{self.endpoint}"

    @property
    def nav_source(self) -> NavSource | None:
        if self.menu_section is MenuSection.HIDDEN:
            return None
        return NavSource(
            section=self.menu_section,
            label=self.label,
            endpoint=self.route,
            match=self.route,
            order=self.order,
            icon=self.icon,
            group=self.menu_group,
        )

    def render(self) -> str:
        response = requests.get(self.url)
        response.raise_for_status()
        lines = response.iter_lines(decode_unicode=True)
        markdown_html = Markdown(*lines).html
        return render_template(
            "admin/markdown.html",
            active_menu=self.endpoint,
            page_title=self.label,
            markdown_html=markdown_html,
        )


class PageView:
    endpoint: str = ""
    label: str = ""
    template: str = ""
    path: str | None = None
    icon: str | None = None
    order: int = 100
    menu_section: MenuSection = MenuSection.HIDDEN
    menu_group: str | None = None

    @property
    def route(self) -> str:
        return f"admin.{self.endpoint}"

    @property
    def rule(self) -> str:
        return self.path or f"/admin/{self.endpoint}"

    @property
    def nav_source(self) -> NavSource | None:
        if self.menu_section is MenuSection.HIDDEN:
            return None
        return NavSource(
            section=self.menu_section,
            label=self.label,
            endpoint=self.route,
            match=self.route,
            order=self.order,
            icon=self.icon,
            group=self.menu_group,
        )

    def context(self) -> dict[str, Any]:
        return {}

    def render(self) -> str:
        return render_template(
            self.template,
            active_menu=self.endpoint,
            page_title=self.label,
            **self.context(),
        )

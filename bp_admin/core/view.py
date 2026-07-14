from typing import Any

import requests
from flask import redirect, render_template
from markupsafe import Markup
from sqlalchemy import or_
from sqlalchemy.orm.session import Session
from web.app.urls import url_for
from web.database.model import AppSettings
from web.utils.markdown import Markdown
from werkzeug import Response

from .action import Action
from .column import Column, row_input_name
from .db import apply_fields, next_order, supports_soft_delete
from .enums import MenuSection, Notice
from .field import Field
from .filter import Filter
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
    menu_match: str | None = None
    order: int = 100
    is_home: bool = False

    # List page
    columns: list[Column] = []
    searchable: list[str] = []
    search_placeholder: str | None = None
    page_size: int = 40
    order_by: Any = None
    reorderable: bool = False
    order_field: str = "order"
    filters: list[Filter] = []

    # Create modal
    create_fields: list[Field] = []

    # Detail page
    tabs: list[Tab] = []
    show_back: bool = True

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

        index = 0
        for filter_ in self.filters:
            if filter_.is_divider:
                continue
            if filter_.key is None:
                filter_.key = f"f{index}"
            index += 1

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

    def back_url(self, obj: Any) -> str | None:
        return None

    def order_input_name(self, row_id: Any) -> str:
        return row_input_name(row_id, self.order_field)

    def title(self, obj: Any) -> str:
        return getattr(obj, "name", None) or f"{self.name} #{obj.id}"

    @property
    def create_title(self) -> str:
        return f"Add {self.name}"

    @property
    def delete_title(self) -> str:
        return f"Delete {self.name}"

    @property
    def search_hint(self) -> str:
        return self.search_placeholder or "Search"

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

    @property
    def has_filters(self) -> bool:
        return any(not f.is_divider for f in self.filters)

    def active_filter_args(self, args: Any) -> dict[str, str]:
        active: dict[str, str] = {}
        for filter_ in self.filters:
            if filter_.is_divider or filter_.key is None:
                continue
            value = args.get(filter_.key)
            if value:
                active[filter_.key] = value
        return active

    def apply_filters(self, query: Any, args: Any) -> Any:
        for filter_ in self.filters:
            if filter_.is_divider or filter_.key is None:
                continue
            value = args.get(filter_.key)
            if not value:
                continue
            try:
                query = filter_.apply(query, value)
            except (TypeError, ValueError):
                continue
        return query

    #
    # Operations
    #

    def get_object(self, s: Session, id_: Any) -> Any:
        return s.query(self.model).filter(self.model.id == id_).first()

    def create(self, s: Session, form: Any, files: Any) -> Any:
        obj = self.model()
        apply_fields(obj, self.create_fields, form, files, respect_readonly=False)
        if self.reorderable and getattr(obj, self.order_field, None) is None:
            order_column = getattr(self.model, self.order_field)
            setattr(
                obj, self.order_field, next_order(s.query(self.model), order_column)
            )
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
    show_back = False


class CachedModelView(ModelView):
    def after_write(self, s: Session, obj: Any = None) -> None:
        settings = s.query(AppSettings).first()
        if settings is not None:
            settings.cached_at = None


class UrlView:
    endpoint: str = ""
    label: str = ""
    url: str = ""
    format: str = "markdown"
    cache: bool = False
    icon: str | None = None
    order: int = 100
    menu_section: MenuSection = MenuSection.BOTTOM
    menu_group: str | None = None

    def __init__(self) -> None:
        self._cached: str | None = None

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

    def fetch(self) -> str:
        response = requests.get(self.url)
        response.raise_for_status()
        return response.text

    def content(self) -> str:
        if self.cache and self._cached is not None:
            return self._cached
        raw = self.fetch()
        if self.format == "markdown":
            html = str(Markdown(*raw.splitlines()).html)
        elif self.format == "html":
            html = raw
        else:
            html = str(Markup('<pre class="mb-0">{}</pre>').format(raw))
        if self.cache:
            self._cached = html
        return html

    def render(self) -> str:
        return render_template(
            "admin/templates/url.html",
            active_menu=self.endpoint,
            page_title=self.label,
            content=self.content(),
        )


class TemplateView:
    endpoint: str = ""
    label: str = ""
    template: str = ""
    path: str | None = None
    icon: str | None = None
    order: int = 100
    menu_section: MenuSection = MenuSection.HIDDEN
    menu_group: str | None = None
    menu_match: str | None = None
    accepts_post: bool = False

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

    def post(self) -> Response | str:
        return redirect(url_for(self.route))


class ActionView:
    endpoint: str = ""
    label: str = ""
    icon: str | None = None
    order: int = 100
    menu_section: MenuSection = MenuSection.BOTTOM
    menu_group: str | None = None
    confirm: str | None = None
    redirect_endpoint: str | None = None

    @property
    def route(self) -> str:
        return f"admin.{self.endpoint}"

    @property
    def rule(self) -> str:
        return f"/admin/{self.endpoint}"

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
            is_action=True,
            confirm=self.confirm,
        )

    def run(self) -> None:
        pass

    def dispatch(self) -> Response:
        self.run()
        target = self.redirect_endpoint or self.route
        return redirect(url_for(target, saved=Notice.DONE))

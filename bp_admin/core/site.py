"""The :class:`AdminSite` registry.

Holds the registered :class:`ModelView` instances plus any manual links to
fully-custom pages, generates the Flask URL rules for each view, and builds the
sidebar menu (including dropdown groups) exposed to templates.
"""

from __future__ import annotations

from typing import Any, Callable

from flask import Blueprint

from . import handlers
from .view import ModelView


class AdminSite:
    def __init__(self) -> None:
        self.views: list[ModelView] = []
        self.links: list[dict[str, Any]] = []

    #
    # Registration
    #

    def register(self, view: ModelView | type[ModelView]) -> ModelView:
        instance = view() if isinstance(view, type) else view
        self.views.append(instance)
        return instance

    def add_link(
        self,
        label: str,
        endpoint: str,
        *,
        icon: str | None = None,
        order: int = 100,
        group: str | None = None,
        section: str = "main",
        match: str | None = None,
    ) -> None:
        self.links.append(
            {
                "label": label,
                "endpoint": endpoint,
                "icon": icon,
                "order": order,
                "group": group,
                "section": section,
                "match": match or endpoint,
            }
        )

    #
    # Flask wiring
    #

    def init_blueprint(self, bp: Blueprint) -> None:
        for view in self.views:
            self._register_view(bp, view)
        bp.context_processor(lambda: {"admin_menu": self.build_menu()})

    def _register_view(self, bp: Blueprint, view: ModelView) -> None:
        e = view.endpoint
        slug = view.slug

        bp.add_url_rule(
            f"/admin/{slug}",
            endpoint=e,
            view_func=self._bind(handlers.list_endpoint, view),
            methods=["GET", "POST"],
        )
        if view.can_create:
            bp.add_url_rule(
                f"/admin/{slug}/new",
                endpoint=f"{e}_create",
                view_func=self._bind(handlers.create_endpoint, view),
                methods=["POST"],
            )
        if view.has_detail:
            bp.add_url_rule(
                f"/admin/{slug}/<int:id_>",
                endpoint=f"{e}_detail",
                view_func=self._bind_id(handlers.detail_endpoint, view),
                methods=["GET"],
            )
            bp.add_url_rule(
                f"/admin/{slug}/<int:id_>/tab/<tab_key>",
                endpoint=f"{e}_tab",
                view_func=self._bind_tab(handlers.tab_endpoint, view),
                methods=["POST"],
            )
            if view.actions:
                bp.add_url_rule(
                    f"/admin/{slug}/<int:id_>/action/<name>",
                    endpoint=f"{e}_action",
                    view_func=self._bind_action(handlers.action_endpoint, view),
                    methods=["POST"],
                )
        if view.can_delete:
            bp.add_url_rule(
                f"/admin/{slug}/<int:id_>/delete",
                endpoint=f"{e}_delete",
                view_func=self._bind_id(handlers.delete_endpoint, view),
                methods=["POST"],
            )

    #
    # View-function binders (capture the view, expose url args by name)
    #

    @staticmethod
    def _bind(func: Callable, view: ModelView) -> Callable:
        def endpoint() -> Any:
            return func(view)

        endpoint.__name__ = f"{view.endpoint}_{func.__name__}"
        return endpoint

    @staticmethod
    def _bind_id(func: Callable, view: ModelView) -> Callable:
        def endpoint(id_: Any) -> Any:
            return func(view, id_)

        endpoint.__name__ = f"{view.endpoint}_{func.__name__}"
        return endpoint

    @staticmethod
    def _bind_tab(func: Callable, view: ModelView) -> Callable:
        def endpoint(id_: Any, tab_key: str) -> Any:
            return func(view, id_, tab_key)

        endpoint.__name__ = f"{view.endpoint}_{func.__name__}"
        return endpoint

    @staticmethod
    def _bind_action(func: Callable, view: ModelView) -> Callable:
        def endpoint(id_: Any, name: str) -> Any:
            return func(view, id_, name)

        endpoint.__name__ = f"{view.endpoint}_{func.__name__}"
        return endpoint

    #
    # Menu
    #

    def build_menu(self) -> dict[str, list[dict[str, Any]]]:
        sections: dict[str, dict[str, dict[str, Any]]] = {"main": {}, "bottom": {}}
        flat: dict[str, list[dict[str, Any]]] = {"main": [], "bottom": []}

        def item_for_view(view: ModelView) -> dict[str, Any]:
            return {
                "type": "link",
                "label": view.name_plural,
                "icon": view.icon,
                "endpoint": f"admin.{view.endpoint}",
                "match": f"admin.{view.endpoint}",
                "order": view.order,
            }

        def item_for_link(link: dict[str, Any]) -> dict[str, Any]:
            return {
                "type": "link",
                "label": link["label"],
                "icon": link["icon"],
                "endpoint": link["endpoint"],
                "match": link["match"],
                "order": link["order"],
            }

        entries: list[tuple[str, str | None, int, str | None, dict[str, Any]]] = []
        for view in self.views:
            entries.append(
                (
                    view.menu_section,
                    view.menu_group,
                    view.order,
                    view.icon,
                    item_for_view(view),
                )
            )
        for link in self.links:
            entries.append(
                (
                    link["section"],
                    link["group"],
                    link["order"],
                    link["icon"],
                    item_for_link(link),
                )
            )

        for section, group, order, icon, item in entries:
            bucket = flat.setdefault(section, [])
            if group is None:
                bucket.append(item)
            else:
                groups = sections.setdefault(section, {})
                if group not in groups:
                    group_item: dict[str, Any] = {
                        "type": "group",
                        "label": group,
                        "icon": icon,
                        "order": order,
                        "items": [],
                    }
                    groups[group] = group_item
                    bucket.append(group_item)
                groups[group]["items"].append(item)

        for section in flat:
            flat[section].sort(key=lambda i: (i["order"], i["label"]))
            for item in flat[section]:
                if item["type"] == "group":
                    item["items"].sort(key=lambda i: (i["order"], i["label"]))
        return flat

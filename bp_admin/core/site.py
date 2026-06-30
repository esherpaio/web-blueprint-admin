from typing import Any, Callable

from flask import Blueprint, request

from . import handlers
from .enums import CellFormat, InputType, Op
from .menu import AdminMenu, build_menu
from .view import MarkdownView, ModelView


class AdminSite:
    def __init__(self) -> None:
        self.views: list[ModelView] = []
        self.markdown_views: list[MarkdownView] = []

    #
    # Registration
    #

    def register(
        self, view: ModelView | type[ModelView] | MarkdownView | type[MarkdownView]
    ) -> ModelView | MarkdownView:
        instance = view() if isinstance(view, type) else view
        if isinstance(instance, MarkdownView):
            self.markdown_views.append(instance)
        elif isinstance(instance, ModelView):
            self.views.append(instance)
        else:
            raise TypeError(f"Cannot register {type(instance).__name__} on AdminSite")
        return instance

    #
    # Flask wiring
    #

    def init_blueprint(self, bp: Blueprint) -> None:
        for view in self.views:
            self._register_view(bp, view)
        for markdown_view in self.markdown_views:
            self._register_markdown_view(bp, markdown_view)
        bp.add_app_template_global(Op, "Op")
        bp.add_app_template_global(InputType, "InputType")
        bp.add_app_template_global(CellFormat, "CellFormat")
        bp.context_processor(lambda: {"admin_menu": self.build_menu()})

    def _register_markdown_view(self, bp: Blueprint, view: MarkdownView) -> None:
        bp.add_url_rule(
            f"/admin/{view.endpoint}",
            endpoint=view.endpoint,
            view_func=view.render,
            methods=["GET"],
        )

    def _register_view(self, bp: Blueprint, view: ModelView) -> None:
        e = view.endpoint
        slug = view.slug

        if view.singleton:
            bp.add_url_rule(
                f"/admin/{slug}",
                endpoint=e,
                view_func=self._bind(handlers.singleton_endpoint, view),
                methods=["GET"],
            )
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
            return

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

    def build_menu(self) -> AdminMenu:
        current = request.endpoint or ""
        sources = []
        for view in self.views:
            source = view.nav_source
            if source is not None:
                sources.append(source)
        for markdown_view in self.markdown_views:
            source = markdown_view.nav_source
            if source is not None:
                sources.append(source)
        return build_menu(sources, current)

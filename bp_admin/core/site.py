from typing import Any, Callable

from flask import Blueprint, redirect, request, url_for

from . import handlers
from .enums import CellFormat, InputType, Op
from .menu import AdminMenu, build_menu
from .view import ModelView, TemplateView, UrlView


class AdminSite:
    def __init__(self) -> None:
        self.views: list[ModelView] = []
        self.url_views: list[UrlView] = []
        self.template_views: list[TemplateView] = []

    #
    # Registration
    #

    def register(
        self,
        view: (type[ModelView] | type[UrlView] | type[TemplateView]),
    ) -> ModelView | UrlView | TemplateView:
        instance = view()
        if isinstance(instance, UrlView):
            self.url_views.append(instance)
        elif isinstance(instance, TemplateView):
            self.template_views.append(instance)
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
        for url_view in self.url_views:
            self._register_url_view(bp, url_view)
        for template_view in self.template_views:
            self._register_template_view(bp, template_view)
        self._register_home(bp)
        bp.add_app_template_global(Op, "Op")
        bp.add_app_template_global(InputType, "InputType")
        bp.add_app_template_global(CellFormat, "CellFormat")
        bp.context_processor(lambda: {"admin_menu": self.build_menu()})

    def _register_home(self, bp: Blueprint) -> None:
        home = next((v for v in self.views if v.is_home), None)
        if home is None:
            return
        bp.add_url_rule(
            "/admin",
            endpoint="index",
            view_func=lambda r: redirect(url_for(r.route)),
            methods=["GET"],
        )

    def _register_url_view(self, bp: Blueprint, view: UrlView) -> None:
        bp.add_url_rule(
            f"/admin/{view.endpoint}",
            endpoint=view.endpoint,
            view_func=view.render,
            methods=["GET"],
        )

    def _register_template_view(self, bp: Blueprint, view: TemplateView) -> None:
        bp.add_url_rule(
            view.rule,
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
        for url_view in self.url_views:
            source = url_view.nav_source
            if source is not None:
                sources.append(source)
        for template_view in self.template_views:
            source = template_view.nav_source
            if source is not None:
                sources.append(source)
        return build_menu(sources, current)

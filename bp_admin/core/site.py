import os
from typing import Any, Callable

from flask import Blueprint, redirect, request, url_for
from jinja2 import ChoiceLoader, FileSystemLoader
from web.app.meta import Meta
from web.auth import authorize_user
from web.database.model import UserRoleLevel
from werkzeug import Response

from . import handlers
from .action import Action, ApiAction
from .enums import AttrType, InputType, Op
from .menu import AdminMenu, build_menu
from .utils import button_class, capfirst
from .view import ActionView, ModelView, TemplateView, UrlView

_ENGINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENGINE_TEMPLATES = os.path.join(_ENGINE_DIR, "templates")
_ENGINE_STATIC = os.path.join(_ENGINE_DIR, "static")


class AdminSite:
    name = "admin"
    static_url_path = "/admin/static"
    auth_role = UserRoleLevel.ADMIN
    meta_title = "Admin"

    def __init__(self) -> None:
        self.views: list[ModelView] = []
        self.url_views: list[UrlView] = []
        self.template_views: list[TemplateView] = []
        self.action_views: list[ActionView] = []
        self.account_actions: list[Action] = [
            ApiAction(
                "logout",
                "Logout",
                method="DELETE",
                endpoint="/api/v1/sessions",
                redirect="/",
                icon="bi-box-arrow-right",
            ),
        ]

    #
    # Registration
    #

    def register(
        self,
        view: (type[ModelView] | type[UrlView] | type[TemplateView] | type[ActionView]),
    ) -> ModelView | UrlView | TemplateView | ActionView:
        instance = view()
        if isinstance(instance, UrlView):
            self.url_views.append(instance)
        elif isinstance(instance, TemplateView):
            self.template_views.append(instance)
        elif isinstance(instance, ActionView):
            self.action_views.append(instance)
        elif isinstance(instance, ModelView):
            self.views.append(instance)
        else:
            raise TypeError(f"Cannot register {type(instance).__name__} on AdminSite")
        return instance

    #
    # Flask wiring
    #

    def build_blueprint(
        self,
        import_name: str,
        template_folder: str | None = None,
    ) -> Blueprint:
        bp = Blueprint(
            name=self.name,
            import_name=import_name,
            static_folder=_ENGINE_STATIC,
            static_url_path=self.static_url_path,
        )
        loaders: list[FileSystemLoader] = []
        if template_folder is not None:
            loaders.append(FileSystemLoader(template_folder))
        loaders.append(FileSystemLoader(_ENGINE_TEMPLATES))
        bp.jinja_loader = ChoiceLoader(loaders)  # type: ignore[assignment]
        self._register(bp)
        bp.before_request(self._authorize)
        bp.context_processor(self._context)
        return bp

    def _register(self, bp: Blueprint) -> None:
        for view in self.views:
            self._register_view(bp, view)
        for url_view in self.url_views:
            self._register_url_view(bp, url_view)
        for template_view in self.template_views:
            self._register_template_view(bp, template_view)
        for action_view in self.action_views:
            self._register_action_view(bp, action_view)
        self._register_home(bp)
        bp.add_app_template_global(Op, "Op")
        bp.add_app_template_global(InputType, "InputType")
        bp.add_app_template_global(AttrType, "AttrType")
        bp.add_app_template_global(button_class, "button_class")
        bp.add_app_template_filter(capfirst, "capfirst")

    def _authorize(self) -> Response | None:
        return authorize_user(self.auth_role)

    def _context(self) -> dict[str, Any]:
        return {
            "meta": Meta(title=self.meta_title, robots="noindex,nofollow"),
            "admin_menu": self.build_menu(),
            "account_actions": self.account_actions,
        }

    def _register_home(self, bp: Blueprint) -> None:
        home = next((v for v in self.views if v.is_home), None)
        if home is None:
            return
        bp.add_url_rule(
            "/admin",
            endpoint="index",
            view_func=lambda: redirect(url_for(home.route)),
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
        methods = ["GET", "POST"] if view.accepts_post else ["GET"]

        def endpoint() -> Any:
            if request.method == "POST":
                return view.post()
            return view.render()

        endpoint.__name__ = view.endpoint
        bp.add_url_rule(
            view.rule,
            endpoint=view.endpoint,
            view_func=endpoint,
            methods=methods,
        )

    def _register_action_view(self, bp: Blueprint, view: ActionView) -> None:
        bp.add_url_rule(
            view.rule,
            endpoint=view.endpoint,
            view_func=view.dispatch,
            methods=["POST"],
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
        for action_view in self.action_views:
            source = action_view.nav_source
            if source is not None:
                sources.append(source)
        return build_menu(sources, current)

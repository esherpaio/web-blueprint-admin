from typing import Any, Callable

from markupsafe import Markup
from sqlalchemy.orm.session import Session

from .enums import LinkMode, Size, Style
from .field import Field
from .utils import resolve_href


class Action:
    def __init__(
        self,
        name: str,
        label: str,
        handler: Callable[[Session, Any, dict[str, Any]], None] | None = None,
        *,
        fields: list[Field] | None = None,
        style: Style | str = Style.PRIMARY,
        size: Size | str | None = None,
        icon: str | None = None,
        confirm: str | None = None,
        text: str | None = None,
        irreversible: bool = False,
        visible: Callable[[Any], bool] | None = None,
        tab: str | None = None,
    ) -> None:
        self.name = name
        self.label = label
        self.handler = handler
        self.fields = fields or []
        self.style = style
        self.size = size
        self.icon = icon
        self.confirm = confirm
        self.text = text
        self.irreversible = irreversible
        self._visible = visible
        self.tab = tab

    @property
    def modal_id(self) -> str:
        return f"modal-action-{self.name}"

    @property
    def notice(self) -> Markup | None:
        if not self.irreversible:
            return None
        return Markup("<strong>This action is irreversible.</strong>")

    @property
    def has_modal(self) -> bool:
        return bool(self.fields) or self.text is not None

    @property
    def is_api(self) -> bool:
        return False

    @property
    def is_link(self) -> bool:
        return False

    def is_visible(self, obj: Any) -> bool:
        return self._visible(obj) if self._visible is not None else True

    def parse(self, form: Any, files: Any = None) -> dict[str, Any]:
        return {field.name: field.parse(form, files) for field in self.fields}

    def run(self, s: Session, obj: Any, data: dict[str, Any]) -> None:
        if self.handler is not None:
            self.handler(s, obj, data)


class ApiAction(Action):
    def __init__(
        self,
        name: str,
        label: str,
        *,
        method: str,
        endpoint: Callable[[Any], str] | str,
        fields: list[Field] | None = None,
        style: Style | str = Style.PRIMARY,
        icon: str | None = None,
        confirm: str | None = None,
        text: str | None = None,
        irreversible: bool = False,
        redirect: str | None = None,
        visible: Callable[[Any], bool] | None = None,
        tab: str | None = None,
    ) -> None:
        super().__init__(
            name,
            label,
            fields=fields,
            style=style,
            icon=icon,
            confirm=confirm,
            text=text,
            irreversible=irreversible,
            visible=visible,
            tab=tab,
        )
        self.method = method
        self._endpoint = endpoint
        self.redirect = redirect

    @property
    def is_api(self) -> bool:
        return True

    def api_url(self, obj: Any) -> str:
        if callable(self._endpoint):
            return self._endpoint(obj)
        return self._endpoint


class LinkAction(Action):
    def __init__(
        self,
        name: str,
        label: str,
        *,
        endpoint: str | None = None,
        url: str | Callable[[Any], str] | None = None,
        values: dict[str, Any] | Callable[[Any], dict[str, Any]] | None = None,
        target: str | None = None,
        download: bool = False,
        style: Style | str = Style.PRIMARY,
        size: Size | str | None = None,
        icon: str | None = None,
        mode: LinkMode | str = LinkMode.BUTTON,
        visible: Callable[[Any], bool] | None = None,
        tab: str | None = None,
    ) -> None:
        super().__init__(
            name,
            label,
            style=style,
            size=size,
            icon=icon,
            visible=visible,
            tab=tab,
        )
        self.endpoint = endpoint
        self.url = url
        self.values = values
        self.target = target
        self.download = download
        self.mode = mode

    @property
    def is_link(self) -> bool:
        return True

    def href(self, obj: Any = None) -> str | None:
        return resolve_href(
            obj,
            endpoint=self.endpoint,
            url=self.url,
            values=self.values,
        )

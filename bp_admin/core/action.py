from typing import Any, Callable

from sqlalchemy.orm.session import Session

from .field import Field


class Action:
    def __init__(
        self,
        name: str,
        label: str,
        handler: Callable[[Session, Any, dict[str, Any]], None],
        *,
        fields: list[Field] | None = None,
        style: str = "primary",
        icon: str | None = None,
        confirm: str | None = None,
        visible: Callable[[Any], bool] | None = None,
        tab: str | None = None,
    ) -> None:
        self.name = name
        self.label = label
        self.handler = handler
        self.fields = fields or []
        self.style = style
        self.icon = icon
        self.confirm = confirm
        self._visible = visible
        self.tab = tab

    @property
    def modal_id(self) -> str:
        return f"modal-action-{self.name}"

    @property
    def is_api(self) -> bool:
        return False

    def is_visible(self, obj: Any) -> bool:
        return self._visible(obj) if self._visible is not None else True

    def parse(self, form: Any, files: Any = None) -> dict[str, Any]:
        return {field.name: field.parse(form, files) for field in self.fields}

    def run(self, s: Session, obj: Any, data: dict[str, Any]) -> None:
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
        style: str = "primary",
        icon: str | None = None,
        confirm: str | None = None,
        visible: Callable[[Any], bool] | None = None,
        tab: str | None = None,
    ) -> None:
        super().__init__(
            name,
            label,
            _noop_handler,
            fields=fields,
            style=style,
            icon=icon,
            confirm=confirm,
            visible=visible,
            tab=tab,
        )
        self.method = method
        self._endpoint = endpoint

    @property
    def is_api(self) -> bool:
        return True

    def api_url(self, obj: Any) -> str:
        return self._endpoint(obj) if callable(self._endpoint) else self._endpoint


def _noop_handler(s: Session, obj: Any, data: dict[str, Any]) -> None:
    pass

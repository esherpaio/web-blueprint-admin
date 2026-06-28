"""Custom row actions for the declarative admin engine.

An :class:`Action` is a button (optionally opening a modal with a small form)
that runs server-side logic against a single object, e.g. "Update status",
"Add shipment" or "Create refund" on an order. It mirrors the existing custom
admin buttons but in a declarative, reusable way.
"""

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
        success_message: str | None = None,
    ) -> None:
        self.name = name
        self.label = label
        self.handler = handler
        self.fields = fields or []
        self.style = style
        self.icon = icon
        self.confirm = confirm
        self._visible = visible
        self.success_message = success_message

    @property
    def modal_id(self) -> str:
        return f"modal-action-{self.name}"

    def is_visible(self, obj: Any) -> bool:
        return self._visible(obj) if self._visible is not None else True

    def parse(self, form: Any, files: Any = None) -> dict[str, Any]:
        return {field.name: field.parse(form, files) for field in self.fields}

    def run(self, s: Session, obj: Any, data: dict[str, Any]) -> None:
        self.handler(s, obj, data)

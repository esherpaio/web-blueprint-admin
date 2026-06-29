"""App settings — a single-record admin view."""

from typing import Any

from sqlalchemy.orm.session import Session
from web.database.model import AppSettings

from bp_admin.core import FormTab, MenuSection, SingletonView, StringField


class SettingsView(SingletonView):
    model = AppSettings
    name = "Settings"
    name_plural = "Settings"
    endpoint = "settings"
    icon = "bi-gear-wide-connected"
    menu_section = MenuSection.BOTTOM
    order = 20

    tabs = [
        FormTab(
            "General",
            [StringField("banner", readonly=False)],
        ),
    ]

    def after_write(self, s: Session, obj: Any = None) -> None:
        if obj is not None:
            obj.cached_at = None

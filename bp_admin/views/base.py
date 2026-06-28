"""Shared base view for the admin POC pages.

Mirrors the old behaviour of resetting ``AppSettings.cached_at`` after a write
so the public site's cache is rebuilt (previously done with a manual
``patchSettings({cached_at: null})`` API call).
"""

from typing import Any

from sqlalchemy.orm.session import Session
from web.database.model import AppSettings

from bp_admin.core import ModelView


class CachedModelView(ModelView):
    def after_write(self, s: Session, obj: Any = None) -> None:
        settings = s.query(AppSettings).first()
        if settings is not None:
            settings.cached_at = None

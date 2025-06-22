from flask import render_template
from web.database import conn
from web.database.model import AppSettings

from web_bp_admin import admin_bp


@admin_bp.get("/admin/settings")
def settings() -> str:
    with conn.begin() as s:
        settings_ = s.query(AppSettings).first()

    return render_template(
        "admin/settings.html",
        active_menu="settings",
        settings=settings_,
    )

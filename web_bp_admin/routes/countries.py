from flask import render_template
from web.database import conn
from web.database.model import Country

from web_bp_admin import admin_bp


@admin_bp.get("/admin/countries")
def countries() -> str:
    with conn.begin() as s:
        countries = s.query(Country).order_by(Country.name).all()
    return render_template(
        "admin/countries.html",
        active_menu="countries",
        countries=countries,
    )

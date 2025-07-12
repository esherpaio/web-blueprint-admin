import requests
from flask import render_template
from web.utils.markdown import Markdown

from web_bp_admin import admin_bp


@admin_bp.get("/admin/changelog")
def changelog() -> str:
    url = "https://raw.githubusercontent.com/esherpaio/web-framework/main/RELEASE.md"
    response = requests.get(url)
    response.raise_for_status()
    lines = response.iter_lines(decode_unicode=True)
    changelog_html = Markdown(*lines).html
    return render_template(
        "admin/changelog.html",
        active_menu="changelog",
        changelog_html=changelog_html,
    )

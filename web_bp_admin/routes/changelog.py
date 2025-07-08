import os

from flask import render_template
from web.setup import settings
from web.utils.markdown import Markdown

from web_bp_admin import admin_bp


@admin_bp.get("/admin/changelog")
def changelog() -> str:
    changelog_fp = os.path.join(settings.ROOT_DIR, "RELEASE.md")
    with open(changelog_fp, "r") as file_:
        changelog_lines = file_.readlines()
    changelog_html = Markdown(*changelog_lines).html
    return render_template(
        "admin/changelog.html",
        active_menu="changelog",
        changelog_html=changelog_html,
    )

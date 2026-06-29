"""Changelog page — renders the framework RELEASE.md via a markdown view."""

from bp_admin.core import MarkdownView

CHANGELOG_URL = (
    "https://raw.githubusercontent.com/esherpaio/web-framework/main/RELEASE.md"
)


class ChangelogView(MarkdownView):
    endpoint = "changelog"
    label = "Changelog"
    url = CHANGELOG_URL
    icon = "bi-newspaper"
    order = 10

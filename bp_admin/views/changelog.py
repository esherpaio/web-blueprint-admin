from bp_admin.core import MarkdownView


class ChangelogView(MarkdownView):
    endpoint = "changelog"
    label = "Changelog"
    url = "https://raw.githubusercontent.com/esherpaio/web-framework/main/RELEASE.md"
    icon = "bi-newspaper"
    order = 10

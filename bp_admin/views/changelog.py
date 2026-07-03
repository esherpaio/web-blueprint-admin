from bp_admin.core import UrlView


class ChangelogView(UrlView):
    endpoint = "changelog"
    label = "Changelog"
    url = "https://raw.githubusercontent.com/esherpaio/web-framework/main/RELEASE.md"
    icon = "bi-newspaper"
    order = 10
    cache = True

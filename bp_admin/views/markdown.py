"""Generic markdown page view — renders a remote markdown document."""

import requests
from flask import Blueprint, render_template
from web.utils.markdown import Markdown

from bp_admin.core import AdminSite


class MarkdownView:
    def __init__(
        self,
        endpoint: str,
        label: str,
        url: str,
        *,
        icon: str | None = None,
        order: int = 100,
        section: str = "bottom",
    ) -> None:
        self.endpoint = endpoint
        self.label = label
        self.url = url
        self.icon = icon
        self.order = order
        self.section = section

    def render(self) -> str:
        response = requests.get(self.url)
        response.raise_for_status()
        lines = response.iter_lines(decode_unicode=True)
        markdown_html = Markdown(*lines).html
        return render_template(
            "admin/markdown.html",
            active_menu=self.endpoint,
            page_title=self.label,
            markdown_html=markdown_html,
        )

    def register(self, bp: Blueprint, site: AdminSite) -> None:
        bp.add_url_rule(
            f"/admin/{self.endpoint}",
            endpoint=self.endpoint,
            view_func=self.render,
            methods=["GET"],
        )
        site.add_link(
            self.label,
            f"admin.{self.endpoint}",
            icon=self.icon,
            order=self.order,
            section=self.section,
        )

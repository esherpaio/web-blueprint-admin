from html import escape
from html.parser import HTMLParser
from urllib.parse import urlsplit

INLINE_TAGS = frozenset({"a", "b", "br", "i"})
LINK_SCHEMES = frozenset({"http", "https", "mailto"})


def clean_inline(html: str) -> str:
    return _clean(html, INLINE_TAGS)


def clean_text(html: str) -> str:
    return _clean(html, frozenset())


def _clean(html: str, tags: frozenset[str]) -> str:
    cleaner = _Cleaner(tags)
    cleaner.feed(html)
    cleaner.close()
    return cleaner.output()


def _is_safe_link(href: str) -> bool:
    scheme = urlsplit(href).scheme
    return scheme in LINK_SCHEMES or (not scheme and href.startswith("/"))


class _Cleaner(HTMLParser):
    def __init__(self, tags: frozenset[str]) -> None:
        super().__init__()
        self._tags = tags
        self._parts: list[str] = []
        self._open: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in self._tags:
            return
        if tag == "br":
            self._parts.append("<br>")
            return
        attributes = ""
        if tag == "a":
            href = dict(attrs).get("href") or ""
            if not _is_safe_link(href):
                return
            attributes = f' href="{escape(href)}"'
            target = dict(attrs).get("target")
            if target in {"_blank", "_self"}:
                attributes += f' target="{target}"'
            if target == "_blank":
                attributes += ' rel="noopener noreferrer"'
        self._parts.append(f"<{tag}{attributes}>")
        self._open.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag not in self._open:
            return
        while (open_tag := self._open.pop()) != tag:
            self._parts.append(f"</{open_tag}>")
        self._parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self._parts.append(escape(data, quote=False))

    def output(self) -> str:
        closing = "".join(f"</{tag}>" for tag in reversed(self._open))
        return "".join(self._parts) + closing

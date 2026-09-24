from collections.abc import Iterable
from dataclasses import dataclass


@dataclass
class NavSource:
    label: str
    endpoint: str
    match: str
    order: int = 100
    icon: str | None = None
    is_action: bool = False
    confirm: str | None = None
    category: str | None = None


@dataclass
class MenuLink:
    label: str
    endpoint: str
    match: str
    icon: str | None = None
    order: int = 100
    active: bool = False
    is_action: bool = False
    confirm: str | None = None
    category: str | None = None


def build_menu(sources: Iterable[NavSource], current: str) -> list[MenuLink]:
    categories: dict[str | None, list[MenuLink]] = {}
    for source in sorted(sources, key=lambda source: (source.order, source.label)):
        link = MenuLink(
            label=source.label,
            endpoint=source.endpoint,
            match=source.match,
            icon=source.icon,
            order=source.order,
            active=current.startswith(source.match),
            is_action=source.is_action,
            confirm=source.confirm,
            category=source.category,
        )
        categories.setdefault(source.category, []).append(link)
    return [item for items in categories.values() for item in items]

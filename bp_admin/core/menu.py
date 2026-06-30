from collections.abc import Iterable
from dataclasses import dataclass, field

from .enums import MenuSection


@dataclass
class NavSource:
    section: MenuSection
    label: str
    endpoint: str
    match: str
    order: int = 100
    icon: str | None = None
    group: str | None = None


@dataclass
class MenuLink:
    label: str
    endpoint: str
    match: str
    icon: str | None = None
    order: int = 100
    active: bool = False
    is_group: bool = False


@dataclass
class MenuGroup:
    label: str
    icon: str | None = None
    order: int = 100
    items: list[MenuLink] = field(default_factory=list)
    active: bool = False
    is_group: bool = True


@dataclass
class AdminMenu:
    main: list[MenuLink | MenuGroup] = field(default_factory=list)
    bottom: list[MenuLink | MenuGroup] = field(default_factory=list)


def build_menu(sources: Iterable[NavSource], current: str) -> AdminMenu:
    menu = AdminMenu()
    buckets: dict[MenuSection, list[MenuLink | MenuGroup]] = {
        MenuSection.MAIN: menu.main,
        MenuSection.BOTTOM: menu.bottom,
    }
    groups: dict[tuple[MenuSection, str], MenuGroup] = {}

    for source in sources:
        bucket = buckets.get(source.section)
        if bucket is None:
            continue
        link = MenuLink(
            label=source.label,
            endpoint=source.endpoint,
            match=source.match,
            icon=source.icon,
            order=source.order,
            active=current.startswith(source.match),
        )
        if source.group is None:
            bucket.append(link)
            continue
        key = (source.section, source.group)
        group = groups.get(key)
        if group is None:
            group = MenuGroup(label=source.group, icon=source.icon, order=source.order)
            groups[key] = group
            bucket.append(group)
        group.items.append(link)

    for bucket in (menu.main, menu.bottom):
        bucket.sort(key=lambda item: (item.order, item.label))
        for item in bucket:
            if isinstance(item, MenuGroup):
                item.active = any(child.active for child in item.items)
                item.items.sort(key=lambda child: (child.order, child.label))

    return menu

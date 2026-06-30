import math
from dataclasses import dataclass

WINDOW = 3


@dataclass
class Page:
    number: int
    label: str
    active: bool = False
    disabled: bool = False

    @property
    def css_class(self) -> str:
        return " ".join(
            cls
            for cls, on in (("disabled", self.disabled), ("active", self.active))
            if on
        )


def get_pages(offset: int, limit: int, total: int) -> list[Page]:
    if total < 1 or limit < 1:
        return []

    current = offset // limit + 1
    last = math.ceil(total / limit)
    window = range(max(current - WINDOW, 1), min(current + WINDOW, last) + 1)

    pages: list[Page] = []

    def add(number: int, label: str, disabled: bool = False) -> None:
        pages.append(
            Page(
                number=number,
                label=label,
                active=number == current,
                disabled=disabled,
            )
        )

    if current > 1:
        add(1, "«")
    if 1 not in window:
        add(1, "…", disabled=True)
    for number in window:
        add(number, str(number))
    if last not in window:
        add(last, "…", disabled=True)
    if current < last:
        add(last, "»")

    return pages

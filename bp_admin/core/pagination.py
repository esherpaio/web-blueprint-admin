import math
from typing import Any

WINDOW = 3


def get_pages(offset: int, limit: int, total: int) -> list[dict[str, Any]]:
    if total < 1 or limit < 1:
        return []

    current = offset // limit + 1
    last = math.ceil(total / limit)
    window = range(max(current - WINDOW, 1), min(current + WINDOW, last) + 1)

    pages: list[dict[str, Any]] = []

    def add(number: int, name: str, disabled: bool = False) -> None:
        classes = " ".join(
            cls
            for cls, on in (("disabled", disabled), ("active", number == current))
            if on
        )
        pages.append({"number": number, "name": name, "classes": classes})

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

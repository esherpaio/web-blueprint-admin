import math
from typing import Any


def get_pages(offset: int, limit: int, total: int) -> list[dict[str, Any]]:
    def _append_page(number_: int, name_: str, disabled: bool = False) -> None:
        class_list = []
        if disabled:
            class_list.append("disabled")
        if number_ == page:
            class_list.append("active")
        class_str = " ".join(class_list)
        pages.append({"number": number_, "name": name_, "classes": class_str})

    # Initialize
    pages: list = []
    if total < 1:
        return pages
    page = int(offset / limit + 1)
    page_min = 1
    page_max = math.ceil(total / limit)

    # Generate numbers
    numbers = []
    page_steps = 3
    page_begin = page - page_steps if page - page_steps > 0 else 1
    page_final = page + page_steps if page + page_steps < page_max else page_max
    for number in range(page_begin, page_final + 1):
        numbers.append(number)

    # Append pages
    if page > page_min:
        _append_page(page_min, "«")
    if page_min not in numbers:
        _append_page(page_min, "…", disabled=True)
    for number in numbers:
        _append_page(number, str(number))
    if page_max not in numbers:
        _append_page(page_max, "…", disabled=True)
    if page < page_max:
        _append_page(page_max, "»")

    return pages

import math
from collections.abc import Iterator
from dataclasses import dataclass

WINDOW = 3


@dataclass(frozen=True)
class Pagination:
    page: int
    per_page: int
    total: int

    @property
    def pages(self) -> int:
        if self.per_page < 1 or self.total < 1:
            return 0
        return math.ceil(self.total / self.per_page)

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def prev_page(self) -> int:
        return max(self.page - 1, 1)

    @property
    def next_page(self) -> int:
        return min(self.page + 1, self.pages)

    def numbers(self, window: int = WINDOW) -> Iterator[int | None]:
        last = self.pages
        previous = 0
        for number in range(1, last + 1):
            near = abs(number - self.page) <= window
            edge = number in (1, last)
            if not (near or edge):
                continue
            if previous and number - previous > 1:
                yield None
            yield number
            previous = number

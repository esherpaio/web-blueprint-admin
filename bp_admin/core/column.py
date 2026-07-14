from typing import Any, Callable

from markupsafe import Markup, escape
from web.cache import cache
from web.locale import current_locale
from web.setup import config
from web.utils.generators import format_decimal

from .enums import Align, CellFormat, LinkMode, Size, Style
from .field import Field, StringField
from .utils import default_label, resolve_href, resolve_path, resolve_value


def row_input_name(row_id: Any, name: str) -> str:
    return f"rows-{row_id}-{name}"


def base_currency_code(obj: Any = None) -> str:
    country = next(
        (c for c in cache.countries if c.code == config.LOCALE_COUNTRY_CODE),
        None,
    )
    if country is None:
        return ""
    currency = next(
        (c for c in cache.currencies if c.id == country.currency_id),
        None,
    )
    return currency.code if currency else ""


class Column:
    is_link = False

    def __init__(
        self,
        name: str,
        label: str | None = None,
        *,
        editable: bool = False,
        field: Field | None = None,
        format: CellFormat | str | Callable[[Any], Any] | None = None,
        row_format: Callable[[Any], Any] | None = None,
        suffix: str | Callable[[Any], Any] | None = None,
        align: Align | str | None = None,
    ) -> None:
        self.name = name
        self.label = label if label is not None else default_label(name)
        self.editable = editable
        self.field = field if field is not None else StringField(name)
        self.format = format
        self.row_format = row_format
        self.suffix = suffix
        self.align = align

    @property
    def format_name(self) -> str | None:
        return self.format if isinstance(self.format, str) else None

    @property
    def align_class(self) -> str:
        return f"text-{self.align}" if self.align else ""

    def suffix_for(self, obj: Any = None) -> Any:
        if callable(self.suffix):
            return self.suffix(obj) if obj is not None else None
        return self.suffix

    def value(self, obj: Any) -> Any:
        return resolve_path(obj, self.name)

    def input_name(self, row_id: Any) -> str:
        return row_input_name(row_id, self.name)

    def cell_value(self, obj: Any, form_values: Any) -> Any:
        submitted = form_values.get(self.input_name(obj.id))
        if submitted is not None:
            return submitted
        return self.field.value_from_obj(obj)

    def display(self, obj: Any) -> Any:
        if self.row_format is not None:
            return self.row_format(obj)
        value = self.value(obj)
        if callable(self.format):
            return self.format(value)
        return value

    def render(self, obj: Any) -> Markup:
        kind = self.format_name
        if kind == CellFormat.PRICE:
            value = self.value(obj)
            if value is None:
                return Markup("")
            return self._with_suffix(escape(format_decimal(value)), obj)
        if kind == CellFormat.DATETIME:
            value = self.value(obj)
            if value is None:
                return Markup("")
            return escape(current_locale.format_datetime(value))
        if kind == CellFormat.BOOL:
            icon = (
                "bi-check-circle-fill text-success"
                if self.value(obj)
                else "bi-dash-circle text-muted"
            )
            return Markup(f'<i class="bi {icon}"></i>')
        display = self.display(obj)
        if display is None:
            return Markup("")
        return self._with_suffix(escape(display), obj)

    def _with_suffix(self, rendered: Markup, obj: Any) -> Markup:
        suffix = self.suffix_for(obj)
        if not suffix:
            return rendered
        return rendered + escape(f" {suffix}")


class LinkColumn(Column):
    is_link = True

    def __init__(
        self,
        name: str,
        label: str | None = "Actions",
        *,
        text: str | Callable[[Any], str],
        endpoint: str | None = None,
        url: str | Callable[[Any], str] | None = None,
        values: dict[str, Any] | Callable[[Any], dict[str, Any]] | None = None,
        target: str | None = None,
        download: bool = False,
        style: Style | str = Style.PRIMARY,
        size: Size | str | None = Size.SM,
        icon: str | None = None,
        mode: LinkMode | str = LinkMode.BUTTON,
        visible: Callable[[Any], bool] | None = None,
        align: Align | str | None = None,
    ) -> None:
        super().__init__(name, label, align=align)
        self._text = text
        self.endpoint = endpoint
        self.url = url
        self.values = values
        self.target = target
        self.download = download
        self.style = style
        self.size = size
        self.icon = icon
        self.mode = mode
        self._visible = visible

    def is_visible(self, obj: Any = None) -> bool:
        if self._visible:
            return self._visible(obj)
        return True

    def href(self, obj: Any) -> str | None:
        return resolve_href(
            obj,
            endpoint=self.endpoint,
            url=self.url,
            values=self.values,
        )

    def text(self, obj: Any) -> str:
        return resolve_value(self._text, obj)

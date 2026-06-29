"""Product option detail — edit an option and its values (reached from product)."""

from web.database.model import ProductMedia, ProductOption, ProductValue

from bp_admin.core import (
    Column,
    DecimalField,
    FormTab,
    InlineTableTab,
    MenuSection,
    SelectField,
    StringField,
)

from .base import CachedModelView


class ProductOptionView(CachedModelView):
    model = ProductOption
    name = "Option"
    name_plural = "Product options"
    endpoint = "product_options"
    menu_section = MenuSection.HIDDEN
    can_edit = True

    tabs = [
        FormTab(
            "General",
            [StringField("name", readonly=False)],
        ),
        InlineTableTab(
            "Values",
            ProductValue,
            "option_id",
            columns=[
                Column("name"),
                Column("unit_price", editable=True, field=DecimalField("unit_price")),
                Column(
                    "media_id",
                    "Media",
                    editable=True,
                    field=SelectField.from_model(
                        "media_id", ProductMedia, label_attr="id", label="Media"
                    ),
                ),
            ],
            create_fields=[
                StringField("name", required=True),
                DecimalField("unit_price"),
            ],
            order_by=ProductValue.order,
            reorderable=True,
        ),
    ]

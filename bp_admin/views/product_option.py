"""Product option detail — edit an option and its values (reached from product)."""

from sqlalchemy import and_
from web.database.model import File, ProductMedia, ProductOption, ProductValue

from bp_admin.core import (
    CachedModelView,
    Column,
    DecimalField,
    FormTab,
    InlineTableTab,
    MenuSection,
    SelectField,
    StringField,
)


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
            [StringField("name")],
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
                        "media_id",
                        ProductMedia,
                        label="Media",
                        label_fn=lambda m: m.file_.description,
                        where=ProductMedia.file_.has(
                            and_(
                                File.description.isnot(None),
                                File.description != "",
                            )
                        ),
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

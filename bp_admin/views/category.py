"""Category admin view — demonstrates a bulk-editable list plus a tabbed detail
page with a JSON attributes editor and an inline child table (category items)."""

from web.database.model import Category, CategoryItem, Sku

from bp_admin.core import (
    Column,
    FormTab,
    InlineTableTab,
    JsonAttributesField,
    SelectField,
    StringField,
)

from .base import CachedModelView


class CategoryView(CachedModelView):
    model = Category
    name = "Category"
    name_plural = "Categories"
    endpoint = "categories"
    icon = "bi-tags"
    order = 20
    page_size = 50

    searchable = ["name"]
    order_by = [Category.order, Category.id]
    reorderable = True

    can_edit = True

    columns = [
        Column("name"),
    ]

    create_fields = [
        StringField("name", required=True),
    ]

    tabs = [
        FormTab(
            "General",
            [
                StringField("name", required=True, readonly=True),
                JsonAttributesField(readonly=True),
            ],
        ),
        InlineTableTab(
            "Items",
            CategoryItem,
            "category_id",
            columns=[
                Column("sku.name", "SKU"),
            ],
            create_fields=[
                SelectField.from_model(
                    "sku_id",
                    Sku,
                    label="SKU",
                    label_attr="name",
                    order_by=Sku.slug,
                    where=Sku.is_deleted.is_(False),
                ),
            ],
            order_by=CategoryItem.order,
            reorderable=True,
        ),
    ]

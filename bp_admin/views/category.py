"""Category admin view — demonstrates a bulk-editable list plus a tabbed detail
page with a JSON attributes editor and an inline child table (category items)."""

from __future__ import annotations

from web.database.model import Category, CategoryItem, Sku

from bp_admin.core import (
    Column,
    FormTab,
    InlineTableTab,
    IntegerField,
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

    columns = [
        Column("id", "ID"),
        Column("name"),
        Column("order", editable=True, field=IntegerField("order")),
    ]

    create_fields = [
        StringField("name", required=True),
        IntegerField("order"),
    ]

    tabs = [
        FormTab(
            "General",
            [
                StringField("name", required=True, readonly=True),
                IntegerField("order"),
                JsonAttributesField(readonly=True),
            ],
        ),
        InlineTableTab(
            "Items",
            CategoryItem,
            "category_id",
            columns=[
                Column("id", "ID"),
                Column("sku.name", "SKU"),
                Column("order", editable=True, field=IntegerField("order")),
            ],
            create_fields=[
                SelectField.from_model(
                    "sku_id",
                    Sku,
                    label="SKU",
                    label_attr="slug",
                    order_by=Sku.slug,
                    where=Sku.is_deleted.is_(False),
                ),
                IntegerField("order"),
            ],
            order_by=CategoryItem.order,
            reorderable=True,
        ),
    ]

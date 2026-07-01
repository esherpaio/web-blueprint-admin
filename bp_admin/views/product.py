from typing import Any

from web.database.model import (
    Product,
    ProductLink,
    ProductLinkType,
    ProductMedia,
    ProductOption,
    ProductType,
    ShipmentClass,
    Sku,
)

from bp_admin.core import (
    ApiAction,
    BoolField,
    CachedModelView,
    CellFormat,
    Column,
    DecimalField,
    FormTab,
    HtmlField,
    InlineTableTab,
    IntegerField,
    Link,
    LinkColumn,
    MediaTab,
    SelectField,
    StringField,
)


class ProductHtmlField(HtmlField):
    def __init__(self) -> None:
        super().__init__("html", "Description", readonly=False)

    def value_from_obj(self, obj: Any) -> Any:
        return (obj.attributes or {}).get("html")

    def apply(self, obj: Any, value: Any) -> None:
        attributes = dict(obj.attributes or {})
        attributes["html"] = value or ""
        obj.attributes = attributes


class ProductView(CachedModelView):
    model = Product
    name = "Product"
    endpoint = "products"
    icon = "bi-boxes"
    order = 30

    can_create = True
    can_delete = True
    can_edit = True
    searchable = ["name"]
    order_by = [Product.name]

    create_fields = [
        StringField("name", required=True),
    ]

    columns = [
        Column("name"),
        Column("shipment_class.name", "Shipment class"),
        Column("unit_price", format=CellFormat.PRICE),
    ]

    actions = [
        ApiAction(
            "generate_skus",
            "Generate SKUs",
            method="POST",
            endpoint=lambda o: f"/api/v1/products/{o.id}/skus",
            tab="skus",
        ),
    ]

    tabs = [
        FormTab(
            "General",
            [
                StringField("name"),
                SelectField.from_model("type_id", ProductType, readonly=False),
                DecimalField("unit_price", readonly=False),
                SelectField.from_model(
                    "shipment_class_id",
                    ShipmentClass,
                    where=ShipmentClass.is_deleted.is_(False),
                    readonly=False,
                ),
                BoolField("consent_required", readonly=False),
                StringField("file_url", readonly=False),
                StringField("summary", readonly=False),
                ProductHtmlField(),
            ],
        ),
        InlineTableTab(
            "Options",
            ProductOption,
            "product_id",
            columns=[
                Column("name"),
                LinkColumn(
                    "id",
                    "Actions",
                    link=Link(
                        "View",
                        endpoint="admin.product_options_detail",
                        values=lambda o: {"id_": o.id},
                    ),
                    align="end",
                ),
            ],
            create_fields=[StringField("name", required=True)],
            order_by=ProductOption.order,
            reorderable=True,
        ),
        MediaTab(
            "Media",
            ProductMedia,
            "product_id",
            path_prefix=lambda p: ("product", p.slug),
        ),
        InlineTableTab(
            "Links",
            ProductLink,
            "product_id",
            columns=[
                Column("type_.name", "Type"),
                Column("sku.name", "SKU"),
            ],
            create_fields=[
                SelectField.from_model("type_id", ProductLinkType, label="Type"),
                SelectField.from_model(
                    "sku_id",
                    Sku,
                    label="SKU",
                    order_by=Sku.slug,
                    where=Sku.is_deleted.is_(False),
                ),
            ],
        ),
        InlineTableTab(
            "SKUs",
            Sku,
            "product_id",
            columns=[
                Column("number", editable=True, field=StringField("number")),
                Column(
                    "details",
                    "Options",
                    format=lambda sds: "<br>".join(
                        f"{sd.option.name}: {sd.value.name}" for sd in sds
                    ),
                ),
                Column("stock", editable=True, field=IntegerField("stock")),
                Column(
                    "is_visible",
                    "Visible",
                    editable=True,
                    field=BoolField("is_visible"),
                ),
            ],
            can_create=False,
        ),
    ]

"""Products list + detail — general, options, media, links and SKUs tabs."""

import itertools
from typing import Any

from markupsafe import Markup
from sqlalchemy.orm.session import Session
from web.api.utils.sku import get_sku_unit_price
from web.database.model import (
    Product,
    ProductLink,
    ProductLinkType,
    ProductMedia,
    ProductOption,
    ProductType,
    ProductValue,
    ShipmentClass,
    Sku,
    SkuDetail,
)
from web.utils.generators import gen_slug

from bp_admin.core import (
    Action,
    BoolField,
    CachedModelView,
    CellFormat,
    Column,
    DecimalField,
    FormTab,
    HtmlField,
    InlineTableTab,
    IntegerField,
    MediaTab,
    SelectField,
    StringField,
)


class ProductHtmlField(HtmlField):
    """Edit the rich-text body stored in ``Product.attributes['html']``."""

    def __init__(self) -> None:
        super().__init__("html", "Description", readonly=False)

    def value_from_obj(self, obj: Any) -> Any:
        return (obj.attributes or {}).get("html")

    def apply(self, obj: Any, value: Any) -> None:
        attributes = dict(obj.attributes or {})
        attributes["html"] = value or ""
        obj.attributes = attributes


def _option_view(option_id: int) -> Markup:
    return Markup(
        f'<a class="btn btn-sm btn-outline-primary" '
        f'href="/admin/product_options/{option_id}">View</a>'
    )


def _sku_options(details: list) -> Markup:
    return Markup("<br>".join(f"{d.option.name}: {d.value.name}" for d in details))


def _generate_skus(s: Session, product: Product, data: dict) -> None:
    existing = s.query(Sku).filter_by(product_id=product.id).all()
    options = [o for o in product.options if not o.is_deleted]
    value_id_sets = [[v.id for v in o.values if not v.is_deleted] for o in options]
    for value_ids in itertools.product(*value_id_sets):
        sku = next((x for x in existing if x.value_ids == sorted(value_ids)), None)
        if sku is not None:
            sku.is_deleted = False
            continue
        values = s.query(ProductValue).filter(ProductValue.id.in_(value_ids)).all()
        slug = gen_slug("-".join([product.name, *(v.name for v in values)]))
        sku = Sku(
            product_id=product.id,
            slug=slug,
            stock=1,
            is_visible=True,
            unit_price=get_sku_unit_price(product, values),
        )
        s.add(sku)
        s.flush()
        s.add_all(
            SkuDetail(sku_id=sku.id, option_id=v.option_id, value_id=v.id)
            for v in values
        )


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

    create_fields = [StringField("name", required=True)]

    columns = [
        Column("name", "Name"),
        Column("shipment_class.name", "Shipment class"),
        Column("unit_price", "Price", format=CellFormat.PRICE),
    ]

    actions = [Action("generate_skus", "Generate SKUs", _generate_skus, tab="skus")]

    tabs = [
        FormTab(
            "General",
            [
                StringField("name"),
                SelectField.from_model("type_id", ProductType, readonly=False),
                SelectField.from_model(
                    "shipment_class_id",
                    ShipmentClass,
                    where=ShipmentClass.is_deleted.is_(False),
                    readonly=False,
                ),
                DecimalField("unit_price", readonly=False),
                BoolField("consent_required", readonly=False),
                StringField("file_url", "Download link", readonly=False),
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
                Column("id", "Actions", format=_option_view, align="end"),
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
                Column("details", "Options", format=_sku_options),
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

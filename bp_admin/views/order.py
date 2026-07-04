from decimal import Decimal

from markupsafe import Markup
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from web.database.model import (
    Billing,
    Invoice,
    Order,
    OrderLine,
    OrderStatus,
    OrderStatusId,
    Refund,
    Shipment,
    Shipping,
    SkuDetail,
)
from web.locale import current_locale
from web.utils.generators import format_decimal

from bp_admin.core import (
    ApiAction,
    CellFormat,
    Column,
    DecimalField,
    FormTab,
    InlineTableTab,
    LinkAction,
    LinkColumn,
    ModelView,
    SelectField,
    StringField,
    TemplateView,
    TextAreaField,
)

_STATUS_COLOR = {
    OrderStatusId.PENDING: "text-bg-danger",
    OrderStatusId.PAID: "text-bg-warning",
    OrderStatusId.IN_PROGRESS: "text-bg-primary",
    OrderStatusId.READY: "text-bg-primary",
    OrderStatusId.COMPLETED: "text-bg-success",
}


def _price_label(value: Decimal | None, currency: str | None) -> str:
    if value is None:
        return ""
    return f"{format_decimal(value)} {currency or ''}".strip()


def _order_status_label(status: OrderStatus | None) -> Markup:
    if status is None:
        return Markup("")
    color = _STATUS_COLOR.get(status.id, "text-bg-secondary")
    return Markup(f'<span class="badge {color}">{status.name}</span>')


def _sku_details_label(sku_details: list[SkuDetail]) -> Markup:
    return Markup(
        "<small>"
        + "<br>".join(f"{d.option.name}: {d.value.name}" for d in sku_details)
        + "</small>"
    )


def _address_label(address, *, with_vat: bool = False) -> str:
    lines = [
        f"{address.first_name} {address.last_name}".strip(),
        address.address,
        f"{address.zip_code} {address.city}".strip(),
        address.state,
        address.country.name if address.country else None,
        address.email,
        address.phone,
        address.company,
    ]
    if with_vat:
        lines.append(getattr(address, "vat", None))
    return "\n".join(line for line in lines if line)


class OrderView(ModelView):
    model = Order
    name = "Order"
    endpoint = "orders"
    icon = "bi-receipt-cutoff"
    order = 10
    order_by = [Order.id.desc()]
    can_edit = True
    is_home = True

    searchable = ["billing.full_name", "shipment.url", "status.name"]
    search_placeholder = "Search by customer, tracking or status"

    columns = [
        Column("id", "ID"),
        Column("created_at", "Date", format=CellFormat.DATETIME),
        Column("billing.full_name", "Customer"),
        Column("status", format=_order_status_label),
        Column("total_price", format=CellFormat.PRICE),
    ]

    actions = [
        LinkAction(
            "add",
            "Add",
            endpoint="admin.order_create",
            icon="bi-plus-square",
        ),
        ApiAction(
            "status",
            "Update status",
            method="PATCH",
            endpoint=lambda o: f"/api/v1/orders/{o.id}",
            fields=[SelectField.from_model("status_id", OrderStatus)],
            visible=lambda o: o.is_paid or o.is_in_progress,
        ),
        ApiAction(
            "shipment",
            "Add shipment",
            method="POST",
            endpoint=lambda o: f"/api/v1/orders/{o.id}/shipments",
            fields=[StringField("url", "Tracking URL", readonly=False)],
            style="warning",
            text="Adding a tracking URL marks this order as shipped and notifies the customer by email.",
            visible=lambda o: not o.is_pending,
            tab="shipments",
        ),
        ApiAction(
            "cancel",
            "Cancel order",
            method="DELETE",
            endpoint=lambda o: f"/api/v1/orders/{o.id}",
            style="warning",
            text="Cancelling this order refunds the customer and restocks the items. This action is irreversible.",
            visible=lambda o: o.is_pending,
        ),
        ApiAction(
            "refund",
            "Create refund",
            method="POST",
            endpoint=lambda o: f"/api/v1/orders/{o.id}/refunds",
            fields=[DecimalField("total_price", readonly=False)],
            style="warning",
            text="Refunds are processed immediately and cannot be undone. Enter the amount to refund to the customer.",
            visible=lambda o: o.is_refundable,
            tab="refunds",
        ),
    ]

    tabs = [
        FormTab(
            "Details",
            [
                StringField("id"),
                StringField(
                    "created_at",
                    format=lambda d: current_locale.format_datetime(d),
                ),
                StringField("status", value="status.name"),
                StringField("shipment_name", "Shipment"),
                StringField(
                    "shipment_price",
                    value=lambda o: _price_label(o.shipment_price, o.currency_code),
                ),
                StringField("coupon_code"),
                StringField(
                    "discount",
                    value=lambda o: _price_label(o.discount_price, o.currency_code),
                ),
                StringField("vat_percentage", "VAT", suffix="%"),
                StringField(
                    "total_price",
                    value=lambda o: _price_label(o.total_price, o.currency_code),
                ),
                TextAreaField(
                    "shipping",
                    value=lambda o: _address_label(o.shipping),
                    rows=6,
                ),
                TextAreaField(
                    "billing",
                    value=lambda o: _address_label(o.billing, with_vat=True),
                    rows=6,
                ),
            ],
            key="details",
        ),
        InlineTableTab(
            "Items",
            OrderLine,
            "order_id",
            columns=[
                Column("sku.product.name", "Name"),
                Column("sku.details", "Options", format=_sku_details_label),
                Column("quantity"),
                Column("total_price", format=CellFormat.PRICE),
                LinkColumn(
                    "id",
                    text="Open URL",
                    url=lambda o: o.sku.product.file_url,
                    target="_blank",
                    align="end",
                ),
            ],
            order_by=OrderLine.id,
            can_create=False,
            can_delete=False,
            key="items",
        ),
        InlineTableTab(
            "Invoices",
            Invoice,
            "order_id",
            columns=[
                Column("number"),
                Column("expires_at", format=CellFormat.DATETIME),
                Column("paid_at", format=CellFormat.DATETIME),
                LinkColumn(
                    "id",
                    text="Download",
                    url=lambda o: f"/api/v1/orders/{o.order_id}/invoices/{o.id}/pdf",
                    align="end",
                ),
            ],
            order_by=Invoice.id,
            can_create=False,
            can_delete=False,
            key="invoices",
        ),
        InlineTableTab(
            "Shipments",
            Shipment,
            "order_id",
            columns=[
                Column("carrier"),
                Column("code"),
                LinkColumn(
                    "url",
                    "Url",
                    text=lambda o: o.url,
                    url=lambda o: o.url,
                    target="_blank",
                    mode="text",
                ),
            ],
            order_by=Shipment.id,
            can_create=False,
            can_delete=False,
            key="shipments",
        ),
        InlineTableTab(
            "Refunds",
            Refund,
            "order_id",
            columns=[
                Column("number"),
                Column("total_price", format=CellFormat.PRICE),
                LinkColumn(
                    "id",
                    text="Download",
                    url=lambda o: f"/api/v1/orders/{o.order_id}/refunds/{o.id}/pdf",
                    align="end",
                ),
            ],
            order_by=Refund.id,
            can_create=False,
            can_delete=False,
            key="refunds",
        ),
    ]

    def get_object(self, s: Session, id_):
        return (
            s.query(Order)
            .options(
                joinedload(Order.billing),
                joinedload(Order.billing, Billing.country),
                joinedload(Order.invoice),
                joinedload(Order.shipments),
                joinedload(Order.shipping),
                joinedload(Order.shipping, Shipping.country),
                joinedload(Order.status),
            )
            .filter(Order.id == id_)
            .first()
        )

    def apply_search(self, query, search):
        if not search:
            return query
        like = f"%{search}%"
        return (
            query.outerjoin(Order.billing)
            .outerjoin(Order.shipments)
            .outerjoin(Order.status)
            .filter(
                or_(
                    Billing.first_name.ilike(like),
                    Billing.last_name.ilike(like),
                    Shipment.url.ilike(like),
                    OrderStatus.name.ilike(like),
                )
            )
            .distinct()
        )

    def title(self, obj) -> str:
        return f"Order #{obj.id}"


class OrderCreateView(TemplateView):
    endpoint = "order_create"
    label = "Add order"
    template = "admin/custom/order_create.html"
    path = "/admin/orders/add"

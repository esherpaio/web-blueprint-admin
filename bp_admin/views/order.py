"""Orders list + detail — engine view with server-side actions."""

from decimal import Decimal

from markupsafe import Markup
from sqlalchemy.orm import Session, joinedload
from web.api.utils.mollie import Mollie
from web.app.urls import url_for
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
)
from web.mail import mail
from web.mail.enum import MailEvent

from bp_admin.core import (
    Action,
    CellFormat,
    Column,
    DecimalField,
    DetailRow,
    DetailSection,
    DetailTab,
    Filter,
    InlineTableTab,
    ModelView,
    SelectField,
    StringField,
)

_STATUS_COLOR = {
    OrderStatusId.PENDING: "text-bg-danger",
    OrderStatusId.PAID: "text-bg-warning",
    OrderStatusId.IN_PROGRESS: "text-bg-primary",
    OrderStatusId.READY: "text-bg-primary",
    OrderStatusId.COMPLETED: "text-bg-success",
}


def _status_badge(status: OrderStatus | None) -> Markup:
    if status is None:
        return Markup("")
    color = _STATUS_COLOR.get(status.id, "text-bg-secondary")
    return Markup(f'<span class="badge {color}">{status.name}</span>')


def _sku_options(details: list) -> Markup:
    return Markup("<br>".join(f"{d.option.name}: {d.value.name}" for d in details))


def _line_open(line: OrderLine) -> Markup:
    if not line.sku.product.file_url:
        return Markup("")
    return Markup(
        f'<a class="btn btn-sm btn-outline-primary" href="{line.sku.product.file_url}"'
        f' target="_blank" rel="noopener">Open</a>'
    )


def _invoice_download(invoice: Invoice) -> Markup:
    url = url_for(
        "admin.orders_id_invoices_id_download",
        order_id=invoice.order_id,
        invoice_id=invoice.id,
    )
    return Markup(
        f'<a class="btn btn-sm btn-outline-primary" href="{url}">Download</a>'
    )


def _refund_download(refund: Refund) -> Markup:
    url = url_for(
        "admin.orders_id_refunds_id_download",
        order_id=refund.order_id,
        refund_id=refund.id,
    )
    return Markup(
        f'<a class="btn btn-sm btn-outline-primary" href="{url}">Download</a>'
    )


def _link(url: str | None) -> Markup:
    if not url:
        return Markup("")
    return Markup(f'<a href="{url}" target="_blank" rel="noopener">{url}</a>')


def _update_status(s: Session, order: Order, data: dict) -> None:
    if data.get("status_id"):
        order.status_id = data["status_id"]


def _add_shipment(s: Session, order: Order, data: dict) -> None:
    url = data.get("url")
    shipment = Shipment(order_id=order.id, url=url)
    s.add(shipment)
    order.status_id = OrderStatusId.COMPLETED
    s.flush()
    mail.trigger_events(
        s,
        MailEvent.ORDER_SHIPPED,
        order.user_id,
        order_id=order.id,
        shipment_url=url,
        billing_email=order.billing.email,
        shipping_email=order.shipping.email,
        shipping_address=order.shipping.full_address,
    )


def _cancel_order(s: Session, order: Order, data: dict) -> None:
    if not order.mollie_id:
        return
    mollie = Mollie()
    payment = mollie.payments.get(order.mollie_id)
    if payment.is_canceled() or not payment.is_cancelable:
        return
    mollie.payments.delete(order.mollie_id)
    order.status_id = OrderStatusId.COMPLETED


def _refund_order(s: Session, order: Order, data: dict) -> None:
    price = data.get("total_price") or Decimal("0.00")
    if price > order.remaining_refund_amount:
        price = order.remaining_refund_amount
    price_vat = round(price * order.vat_rate, 2)
    refund = Refund(order_id=order.id, total_price=abs(price) * -1)
    s.add(refund)
    s.flush()
    mollie = Mollie()
    payment = mollie.payments.get(order.mollie_id)
    mollie_refund = payment.refunds.create(
        {"amount": mollie.gen_amount(price_vat, order.currency_code)}
    )
    refund.mollie_id = mollie_refund.id
    s.flush()
    mail.trigger_events(
        s,
        MailEvent.ORDER_REFUNDED,
        order.user_id,
        order_id=order.id,
        refund_id=refund.id,
        billing_email=order.billing.email,
    )


class OrderView(ModelView):
    model = Order
    name = "Order"
    endpoint = "orders"
    icon = "bi-receipt-cutoff"
    order = 10
    order_by = [Order.id.desc()]
    can_edit = True

    filters = [
        Filter(
            "status_id",
            "Status",
            choices=lambda s: [(st.id, st.name) for st in s.query(OrderStatus).all()],
        )
    ]

    columns = [
        Column("id", "ID"),
        Column("created_at", "Date", format=CellFormat.DATETIME),
        Column("billing.full_name", "Customer"),
        Column("status", "Status", format=_status_badge),
        Column("total_price", "Total", format=CellFormat.PRICE),
    ]

    actions = [
        Action(
            "status",
            "Update status",
            _update_status,
            fields=[SelectField.from_model("status_id", OrderStatus)],
            visible=lambda o: o.is_paid or o.is_in_progress,
        ),
        Action(
            "shipment",
            "Add shipment",
            _add_shipment,
            fields=[StringField("url", "Tracking URL", readonly=False)],
            style="warning",
            visible=lambda o: not o.is_pending,
        ),
        Action(
            "cancel",
            "Cancel order",
            _cancel_order,
            style="warning",
            confirm="Cancel this order?",
            visible=lambda o: o.is_pending,
        ),
        Action(
            "refund",
            "Create refund",
            _refund_order,
            fields=[DecimalField("total_price", readonly=False)],
            style="warning",
            visible=lambda o: o.is_refundable,
        ),
    ]

    tabs = [
        DetailTab(
            "Details",
            [
                DetailSection(
                    "Details",
                    [
                        DetailRow("Order ID", "id"),
                        DetailRow(
                            "Created at", "created_at", format=CellFormat.DATETIME
                        ),
                        DetailRow(
                            "Status",
                            lambda o: _status_badge(o.status),
                            spaced=True,
                        ),
                        DetailRow("Shipment", "shipment_name"),
                        DetailRow(
                            "Shipment price",
                            "shipment_price",
                            format=CellFormat.PRICE,
                            suffix=lambda o: o.currency_code,
                            spaced=True,
                        ),
                        DetailRow("Coupon", "coupon_code"),
                        DetailRow(
                            "Discount",
                            "discount_price",
                            format=CellFormat.PRICE,
                            suffix=lambda o: o.currency_code,
                            spaced=True,
                        ),
                        DetailRow("VAT rate", "vat_percentage", suffix="%"),
                        DetailRow(
                            "Total price",
                            "total_price",
                            format=CellFormat.PRICE,
                            suffix=lambda o: o.currency_code,
                        ),
                    ],
                ),
                DetailSection(
                    "Shipping",
                    [
                        DetailRow(
                            "",
                            lambda o: f"{o.shipping.first_name} {o.shipping.last_name}",
                        ),
                        DetailRow("", "shipping.address"),
                        DetailRow(
                            "",
                            lambda o: f"{o.shipping.zip_code} {o.shipping.city}",
                        ),
                        DetailRow("", "shipping.state", optional=True),
                        DetailRow("", "shipping.country.name", spaced=True),
                        DetailRow("", "shipping.email"),
                        DetailRow("", "shipping.phone", optional=True),
                        DetailRow("", "shipping.company", optional=True),
                    ],
                    width="col-12 col-lg-3",
                    layout="lines",
                ),
                DetailSection(
                    "Billing",
                    [
                        DetailRow(
                            "",
                            lambda o: f"{o.billing.first_name} {o.billing.last_name}",
                        ),
                        DetailRow("", "billing.address"),
                        DetailRow(
                            "",
                            lambda o: f"{o.billing.zip_code} {o.billing.city}",
                        ),
                        DetailRow("", "billing.state", optional=True),
                        DetailRow("", "billing.country.name", spaced=True),
                        DetailRow("", "billing.email"),
                        DetailRow("", "billing.phone", optional=True),
                        DetailRow("", "billing.company", optional=True),
                        DetailRow("", "billing.vat", optional=True),
                    ],
                    width="col-12 col-lg-3",
                    layout="lines",
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
                Column("sku.details", "Options", format=_sku_options),
                Column("quantity", "Quantity"),
                Column("total_price", "Total", format=CellFormat.PRICE),
                Column("id", "", row_format=_line_open, align="end"),
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
                Column("number", "Number"),
                Column("expires_at", "Expires at", format=CellFormat.DATETIME),
                Column("paid_at", "Paid at", format=CellFormat.DATETIME),
                Column("id", "", row_format=_invoice_download, align="end"),
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
                Column("carrier", "Carrier"),
                Column("code", "Code"),
                Column("url", "Tracking URL", row_format=lambda r: _link(r.url)),
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
                Column("number", "Number"),
                Column("total_price", "Total", format=CellFormat.PRICE),
                Column("id", "", row_format=_refund_download, align="end"),
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

    def title(self, obj) -> str:
        return f"Order #{obj.id}"

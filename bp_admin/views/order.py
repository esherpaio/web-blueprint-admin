"""Orders list + detail — engine view with server-side actions."""

from decimal import Decimal

from markupsafe import Markup
from sqlalchemy.orm import Session, joinedload
from web.api.utils.mollie import Mollie
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
    Sku,
    SkuDetail,
)
from web.mail import mail
from web.mail.enum import MailEvent

from bp_admin.core import (
    Action,
    CellFormat,
    Column,
    DecimalField,
    Filter,
    ModelView,
    SelectField,
    StringField,
    TemplateTab,
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


def _detail_context(s: Session, order: Order) -> dict:
    lines = (
        s.query(OrderLine)
        .options(
            joinedload(OrderLine.sku),
            joinedload(OrderLine.sku, Sku.product),
            joinedload(OrderLine.sku, Sku.details),
            joinedload(OrderLine.sku, Sku.details, SkuDetail.option),
            joinedload(OrderLine.sku, Sku.details, SkuDetail.value),
        )
        .filter_by(order_id=order.id)
        .order_by(OrderLine.id)
        .all()
    )
    invoices = s.query(Invoice).filter_by(order_id=order.id).order_by(Invoice.id).all()
    refunds = s.query(Refund).filter_by(order_id=order.id).order_by(Refund.id).all()
    return {
        "order": order,
        "order_lines": lines,
        "invoices": invoices,
        "refunds": refunds,
        "order_status_color_map": _STATUS_COLOR,
    }


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
        TemplateTab(
            "Details",
            "admin/custom/order_detail.html",
            key="details",
            context=_detail_context,
        )
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

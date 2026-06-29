"""Orders list + detail — engine view. Actions reuse the existing JSON API."""

from markupsafe import Markup
from sqlalchemy.orm import Session, joinedload
from web.database.model import (
    Billing,
    Invoice,
    Order,
    OrderLine,
    OrderStatus,
    OrderStatusId,
    Refund,
    Shipping,
    Sku,
    SkuDetail,
)

from bp_admin.core import CellFormat, Column, Filter, ModelView, TemplateTab

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
        "status_ready": OrderStatusId.READY,
    }


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

    tabs = [
        TemplateTab(
            "Details",
            "admin/_engine/orders_detail.html",
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

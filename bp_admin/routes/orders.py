from flask import render_template, request, send_file
from sqlalchemy import or_
from sqlalchemy.orm import contains_eager, joinedload
from web.api import HttpText, json_response
from web.database import conn
from web.database.model import (
    Billing,
    Invoice,
    Order,
    OrderLine,
    OrderStatusId,
    Refund,
    Shipment,
    Shipping,
    Sku,
    SkuDetail,
)
from web.document import get_pdf_path
from web.document.object import gen_invoice_pdf, gen_refund_pdf
from web.i18n import _
from web.utils import remove_file
from werkzeug import Response

from bp_admin import admin_bp
from bp_admin.utils import get_pages

order_status_color_map = {
    OrderStatusId.PENDING: "text-bg-danger",
    OrderStatusId.PAID: "text-bg-warning",
    OrderStatusId.IN_PROGRESS: "text-bg-primary",
    OrderStatusId.READY: "text-bg-primary",
    OrderStatusId.COMPLETED: "text-bg-success",
}


@admin_bp.get("/admin")
@admin_bp.get("/admin/orders")
def orders() -> str:
    limit = request.args.get("l", type=int, default=40)
    page = request.args.get("p", type=int, default=1)
    offset = (limit * page) - limit
    status_id = request.args.get("status", type=int, default=None)
    search = request.args.get("s", type=str, default=None)

    filters = []
    if status_id is not None:
        filters.append(Order.status_id == status_id)
    if search is not None:
        filters.append(
            or_(
                Shipment.url.ilike(f"%{search}%"),
                Billing.full_name.ilike(f"%{search}%"),  # type: ignore[attr-defined]
            )
        )

    with conn.begin() as s:
        orders_len = (
            s.query(Order)
            .join(Order.billing)
            .join(Order.shipments, isouter=True)
            .options(
                contains_eager(Order.billing),
                contains_eager(Order.shipments),
            )
            .filter(*filters)
            .count()
        )
        orders_ = (
            s.query(Order)
            .join(Order.billing)
            .join(Order.status)
            .join(Order.refunds, isouter=True)
            .join(Order.shipments, isouter=True)
            .options(
                contains_eager(Order.status),
                contains_eager(Order.refunds),
                contains_eager(Order.billing),
                contains_eager(Order.shipments),
            )
            .filter(*filters)
            .order_by(Order.id.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    pagination = get_pages(offset, limit, orders_len)
    return render_template(
        "admin/orders.html",
        active_menu="orders",
        order_status_color_map=order_status_color_map,
        search=search,
        status_id=status_id,
        orders=orders_,
        pagination=pagination,
    )


@admin_bp.get("/admin/orders/add")
def orders_add() -> str | Response:
    return render_template(
        "admin/orders_add.html",
        active_menu="orders",
    )


@admin_bp.get("/admin/orders/<int:order_id>")
def orders_id(order_id: int) -> str:
    with conn.begin() as s:
        order_ = (
            s.query(Order)
            .options(
                joinedload(Order.billing),
                joinedload(Order.billing, Billing.country),
                joinedload(Order.invoice),
                joinedload(Order.lines),
                joinedload(Order.refunds),
                joinedload(Order.shipments),
                joinedload(Order.shipping),
                joinedload(Order.shipping, Shipping.country),
                joinedload(Order.status),
            )
            .filter_by(id=order_id)
            .first()
        )
        order_lines = (
            s.query(OrderLine)
            .options(
                joinedload(OrderLine.sku),
                joinedload(OrderLine.sku, Sku.product),
                joinedload(OrderLine.sku, Sku.details),
                joinedload(OrderLine.sku, Sku.details, SkuDetail.option),
                joinedload(OrderLine.sku, Sku.details, SkuDetail.value),
            )
            .filter_by(order_id=order_id)
            .order_by(OrderLine.id)
            .all()
        )
        invoices = (
            s.query(Invoice).filter_by(order_id=order_id).order_by(Invoice.id).all()
        )
        refunds = s.query(Refund).filter_by(order_id=order_id).order_by(Refund.id).all()

    return render_template(
        "admin/orders_id.html",
        active_menu="orders",
        order_status_color_map=order_status_color_map,
        order=order_,
        order_lines=order_lines,
        invoices=invoices,
        refunds=refunds,
        status_ready=OrderStatusId.READY,
    )


@admin_bp.get("/admin/orders/<int:order_id>/invoices/<int:invoice_id>/download")
def orders_id_invoices_id_download(order_id: int, invoice_id: int) -> Response:
    with conn.begin() as s:
        order_ = s.query(Order).filter_by(id=order_id).first()
        if not order_ or not order_.invoice:
            return json_response(404, HttpText.HTTP_404)
        invoice = order_.invoice
        pdf = gen_invoice_pdf(s, order_, invoice)
        pdf_name = _("PDF_INVOICE_FILENAME", invoice_number=invoice.number)
        pdf_path = get_pdf_path(pdf_name)
        pdf.output(pdf_path)
    remove_file(pdf_path, delay_s=20)
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=pdf_name,
    )


@admin_bp.get("/admin/orders/<int:order_id>/refunds/<int:refund_id>/download")
def orders_id_refunds_id_download(order_id: int, refund_id: int) -> Response:
    with conn.begin() as s:
        order_ = s.query(Order).filter_by(id=order_id).first()
        refund = s.query(Refund).filter_by(id=refund_id).first()
        if not order_ or not order_.invoice or not refund:
            return json_response(404, HttpText.HTTP_404)
        invoice = order_.invoice
        pdf = gen_refund_pdf(s, order_, invoice, refund)
        pdf_name = _("PDF_REFUND_FILENAME", refund_number=refund.number)
        pdf_path = get_pdf_path(pdf_name)
        pdf.output(pdf_path)
    remove_file(pdf_path, delay_s=20)
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=pdf_name,
    )

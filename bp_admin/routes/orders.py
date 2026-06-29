from flask import redirect, render_template, send_file, url_for
from web.api import HttpText, json_response
from web.database import conn
from web.database.model import Order, Refund
from web.document import get_pdf_path
from web.document.object import gen_invoice_pdf, gen_refund_pdf
from web.i18n import _
from web.utils import remove_file
from werkzeug import Response

from bp_admin import admin_bp


@admin_bp.get("/admin")
def admin_index() -> Response:
    return redirect(url_for("admin.orders"))


@admin_bp.get("/admin/orders/add")
def orders_add() -> str | Response:
    return render_template(
        "admin/orders_add.html",
        active_menu="orders",
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

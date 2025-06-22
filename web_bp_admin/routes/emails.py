from flask import render_template, request
from web.database import conn
from web.database.model import Email
from web.mail.enum import MailEvent

from web_bp_admin import admin_bp
from web_bp_admin.utils import get_pages


@admin_bp.get("/admin/emails")
def emails() -> str:
    limit = request.args.get("l", type=int, default=40)
    page = request.args.get("p", type=int, default=1)
    offset = (limit * page) - limit

    with conn.begin() as s:
        count = s.query(Email).filter(Email.event_id == MailEvent.WEBSITE_BULK).count()
        emails_ = (
            s.query(Email)
            .filter(Email.event_id == MailEvent.WEBSITE_BULK)
            .order_by(Email.id.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    pagination = get_pages(offset, limit, count)
    return render_template(
        "admin/emails.html",
        active_menu="emails",
        emails=emails_,
        pagination=pagination,
    )

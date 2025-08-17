from flask import render_template
from web.database import conn
from web.database.model import Coupon

from bp_admin import admin_bp


@admin_bp.get("/admin/coupons")
def coupons() -> str:
    with conn.begin() as s:
        coupons_ = (
            s.query(Coupon)
            .filter_by(is_deleted=False)
            .order_by(Coupon.code, Coupon.id)
            .all()
        )

    return render_template(
        "admin/coupons.html",
        active_menu="coupons",
        coupons=coupons_,
    )

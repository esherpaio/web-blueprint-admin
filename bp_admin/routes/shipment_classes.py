from flask import render_template
from web.database import conn
from web.database.model import ShipmentClass

from bp_admin import admin_bp


@admin_bp.get("/admin/shipment-classes")
def shipment_classes() -> str:
    with conn.begin() as s:
        shipment_classes_ = (
            s.query(ShipmentClass)
            .filter_by(is_deleted=False)
            .order_by(ShipmentClass.order, ShipmentClass.id)
            .all()
        )

    return render_template(
        "admin/shipment_classes.html",
        active_menu="shipments",
        shipment_classes=shipment_classes_,
    )

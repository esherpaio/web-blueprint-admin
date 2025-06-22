from flask import render_template
from sqlalchemy.orm import joinedload
from web.database import conn
from web.database.model import ShipmentZone

from web_bp_admin import admin_bp


@admin_bp.get("/admin/shipment-zones")
def shipment_zones() -> str:
    with conn.begin() as s:
        shipment_zones_ = (
            s.query(ShipmentZone)
            .options(
                joinedload(ShipmentZone.country),
                joinedload(ShipmentZone.region),
            )
            .filter_by(is_deleted=False)
            .order_by(ShipmentZone.order, ShipmentZone.id)
            .all()
        )

    return render_template(
        "admin/shipment_zones.html",
        active_menu="shipments",
        shipment_zones=shipment_zones_,
    )

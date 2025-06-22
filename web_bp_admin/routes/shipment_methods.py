from flask import render_template
from sqlalchemy.orm import joinedload
from web.database import conn
from web.database.model import ShipmentClass, ShipmentMethod, ShipmentZone

from web_bp_admin import admin_bp


@admin_bp.get("/admin/shipment-methods")
def shipment_methods() -> str:
    with conn.begin() as s:
        shipment_methods_ = (
            s.query(ShipmentMethod)
            .options(
                joinedload(ShipmentMethod.class_),
                joinedload(ShipmentMethod.zone).joinedload(ShipmentZone.country),
                joinedload(ShipmentMethod.zone).joinedload(ShipmentZone.region),
            )
            .filter_by(is_deleted=False)
            .order_by(
                ShipmentMethod.class_id,
                ShipmentMethod.zone_id,
                ShipmentMethod.unit_price,
                ShipmentMethod.id,
            )
            .all()
        )
        shipment_classes = (
            s.query(ShipmentClass)
            .filter_by(is_deleted=False)
            .order_by(ShipmentClass.name, ShipmentClass.id)
            .all()
        )
        shipment_zones = (
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
        "admin/shipment_methods.html",
        active_menu="shipments",
        shipment_methods=shipment_methods_,
        shipment_classes=shipment_classes,
        shipment_zones=shipment_zones,
    )

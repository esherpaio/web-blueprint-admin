"""Shipment admin views: shipment classes (each with its per-zone pricing) and
shipment zones."""

from sqlalchemy.orm.session import Session
from web.database.model import (
    Country,
    Region,
    ShipmentClass,
    ShipmentMethod,
    ShipmentZone,
)

from bp_admin.core import (
    Column,
    DecimalField,
    FormTab,
    InlineTableTab,
    SelectField,
    StringField,
)

from .base import CachedModelView


def _zone_choices(s: Session) -> list:
    zones = (
        s.query(ShipmentZone)
        .filter(ShipmentZone.is_deleted.is_(False))
        .order_by(ShipmentZone.order, ShipmentZone.id)
        .all()
    )
    choices = []
    for zone in zones:
        if zone.country is not None:
            label = zone.country.name
        elif zone.region is not None:
            label = zone.region.name
        else:
            label = f"Zone {zone.id}"
        choices.append((zone.id, label))
    return choices


class ShipmentClassView(CachedModelView):
    model = ShipmentClass
    name = "Shipment class"
    name_plural = "Shipment classes"
    endpoint = "shipment_classes"
    icon = "bi-truck"
    order = 40

    reorderable = True
    can_create = True
    can_delete = True
    can_edit = True

    order_by = [ShipmentClass.order, ShipmentClass.id]
    columns = [
        Column("name"),
    ]
    create_fields = [
        StringField("name", required=True),
    ]

    tabs = [
        FormTab(
            "General",
            [
                StringField("name", readonly=True, required=True),
            ],
        ),
        InlineTableTab(
            "Zones",
            ShipmentMethod,
            "class_id",
            columns=[
                Column(
                    "name",
                    editable=True,
                    field=StringField("name", required=True),
                ),
                Column(
                    "zone_id",
                    "Zone",
                    editable=True,
                    field=SelectField(
                        "zone_id",
                        "Zone",
                        choices=_zone_choices,
                        coerce=int,
                    ),
                ),
                Column(
                    "unit_price",
                    "Price",
                    editable=True,
                    field=DecimalField("unit_price"),
                ),
            ],
            create_fields=[
                StringField("name", required=True),
                SelectField("zone_id", "Zone", choices=_zone_choices, coerce=int),
                DecimalField("unit_price"),
            ],
            order_by=ShipmentMethod.name,
        ),
    ]


class ShipmentZoneView(CachedModelView):
    model = ShipmentZone
    name = "Shipment zone"
    name_plural = "Shipment zones"
    endpoint = "shipment_zones"
    icon = "bi-geo-alt"
    order = 41

    reorderable = True
    can_create = True
    can_delete = True

    order_by = [ShipmentZone.order, ShipmentZone.id]
    columns = [
        Column("country.name", "Country"),
        Column("region.name", "Region"),
    ]
    create_fields = [
        SelectField.from_model(
            "country_id", Country, label_attr="name", order_by=Country.name
        ),
        SelectField.from_model("region_id", Region, label_attr="name"),
    ]

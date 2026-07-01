from sqlalchemy.orm.session import Session
from web.database.model import (
    Country,
    Region,
    ShipmentClass,
    ShipmentMethod,
    ShipmentZone,
)

from bp_admin.core import (
    BoolField,
    CachedModelView,
    Column,
    DecimalField,
    FormTab,
    InlineTableTab,
    SelectField,
    StringField,
)


def _shipment_zone_label(zone: ShipmentZone) -> str:
    if zone.country is not None:
        return zone.country.name
    if zone.region is not None:
        return zone.region.name
    return f"Zone {zone.id}"


def _shipment_zone_choices(s: Session) -> list:
    zones = (
        s.query(ShipmentZone)
        .filter(ShipmentZone.is_deleted.is_(False))
        .order_by(ShipmentZone.order, ShipmentZone.id)
        .all()
    )
    return [(zone.id, _shipment_zone_label(zone)) for zone in zones]


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
                StringField("name", required=True),
            ],
        ),
        InlineTableTab(
            "Shipment methods",
            ShipmentMethod,
            "class_id",
            columns=[
                Column("name"),
                Column("zone", format=_shipment_zone_label),
                Column(
                    "unit_price",
                    editable=True,
                    field=DecimalField("unit_price"),
                ),
                Column(
                    "requires_billing_phone",
                    "Phone required",
                    editable=True,
                    field=BoolField("requires_billing_phone"),
                ),
            ],
            create_fields=[
                StringField("name", required=True),
                SelectField(
                    "zone_id",
                    "Zone",
                    choices=_shipment_zone_choices,
                    coerce=int,
                ),
                DecimalField("unit_price"),
                BoolField("requires_billing_phone"),
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
            "country_id",
            Country,
            label_attr="name",
            order_by=Country.name,
        ),
        SelectField.from_model(
            "region_id",
            Region,
            label_attr="name",
        ),
    ]

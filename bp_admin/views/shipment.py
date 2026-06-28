"""Shipment admin views — three related list pages grouped under a single
"Shipments" sidebar dropdown."""

from __future__ import annotations

from web.database.model import (
    Country,
    Region,
    ShipmentClass,
    ShipmentMethod,
    ShipmentZone,
)

from bp_admin.core import Column, DecimalField, SelectField, StringField

from .base import CachedModelView


class ShipmentClassView(CachedModelView):
    model = ShipmentClass
    name = "Shipment class"
    name_plural = "Classes"
    endpoint = "shipment_classes"
    icon = "bi-truck"
    menu_group = "Shipments"
    order = 40

    order_by = [ShipmentClass.order, ShipmentClass.id]
    reorderable = True
    columns = [
        Column("name"),
    ]
    create_fields = [
        StringField("name", required=True),
    ]


class ShipmentZoneView(CachedModelView):
    model = ShipmentZone
    name = "Shipment zone"
    name_plural = "Zones"
    endpoint = "shipment_zones"
    icon = "bi-truck"
    menu_group = "Shipments"
    order = 41

    order_by = [ShipmentZone.order, ShipmentZone.id]
    reorderable = True
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


class ShipmentMethodView(CachedModelView):
    model = ShipmentMethod
    name = "Shipment method"
    name_plural = "Methods"
    endpoint = "shipment_methods"
    icon = "bi-truck"
    menu_group = "Shipments"
    order = 42

    order_by = [ShipmentMethod.name]
    columns = [
        Column("name"),
        Column(
            "unit_price",
            "Price",
            editable=True,
            field=DecimalField("unit_price"),
        ),
        Column("class_.name", "Class"),
        Column("zone_id", "Zone"),
    ]
    create_fields = [
        StringField("name", required=True),
        SelectField.from_model(
            "class_id", ShipmentClass, label_attr="name", order_by=ShipmentClass.order
        ),
        SelectField.from_model("zone_id", ShipmentZone, label_attr="id"),
        DecimalField("unit_price"),
    ]

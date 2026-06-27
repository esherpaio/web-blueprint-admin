"""Coupon admin view — demonstrates a modal create form and a custom action
(setting a discount percentage) backed by server-side logic, mirroring the
order-style action buttons."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.orm.session import Session
from web.database.model import Coupon

from bp_admin.core import (
    Action,
    Column,
    DecimalField,
    FormTab,
    IntegerField,
    StringField,
)

from .base import CachedModelView


def _set_percentage(s: Session, coupon: Any, data: dict[str, Any]) -> None:
    percentage = data.get("percentage")
    if percentage is None:
        return
    coupon.amount = None
    coupon.rate = Decimal("1") - (Decimal(percentage) / Decimal("100"))


class CouponView(CachedModelView):
    model = Coupon
    name = "Coupon"
    endpoint = "coupons"
    icon = "bi-ticket-perforated"
    order = 50

    columns = [
        Column("code", editable=True, field=StringField("code", required=True)),
        Column("percentage", "Percentage"),
        Column("amount", "Amount", format="price"),
    ]

    create_fields = [
        StringField("code", required=True),
        DecimalField("amount"),
    ]

    tabs = [
        FormTab(
            "General",
            [
                StringField("code", required=True),
                DecimalField("amount"),
            ],
        ),
    ]

    actions = [
        Action(
            "set_percentage",
            "Set percentage",
            handler=_set_percentage,
            fields=[IntegerField("percentage", required=True)],
            style="warning",
            icon="bi-percent",
        ),
    ]

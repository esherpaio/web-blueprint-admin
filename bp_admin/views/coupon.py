"""Coupon admin view.

A coupon is either a fixed-amount discount or a percentage discount (the model
stores those as mutually exclusive ``amount`` / ``rate`` columns). The
``PercentageField`` and ``AmountField`` below let the admin edit either one as a
plain column: setting one clears the other so the database constraint is always
satisfied.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from web.database.model import Coupon

from bp_admin.core import Column, DecimalField, FormTab, IntegerField, StringField

from .base import CachedModelView


class PercentageField(IntegerField):
    def value_from_obj(self, obj: Any) -> int | None:
        if obj.rate is None:
            return None
        return int(round((1 - obj.rate) * 100))

    def apply(self, obj: Any, value: Any) -> None:
        if value is None:
            return
        obj.rate = Decimal("1") - (Decimal(value) / Decimal("100"))


class AmountField(DecimalField):
    def apply(self, obj: Any, value: Any) -> None:
        if value is None:
            return
        obj.amount = value


class CouponView(CachedModelView):
    model = Coupon
    name = "Coupon"
    endpoint = "coupons"
    icon = "bi-ticket-perforated"
    order = 50

    columns = [
        Column("code", "Code"),
        Column(
            "percentage",
            "Percentage",
            editable=True,
            field=PercentageField("percentage"),
        ),
        Column("amount", "Amount", format="price"),
    ]

    create_fields = [
        StringField("code", required=True),
        AmountField("amount"),
        PercentageField("percentage"),
    ]

    tabs = [
        FormTab(
            "General",
            [
                StringField("code", required=True),
                AmountField("amount"),
                PercentageField("percentage"),
            ],
        ),
    ]

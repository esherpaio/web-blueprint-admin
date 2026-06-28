"""Coupon admin view.

A coupon is either a fixed-amount discount or a percentage discount (the model
stores those as mutually exclusive ``amount`` / ``rate`` columns). The
``PercentageField`` and ``AmountField`` below let the admin edit either one as a
plain column: setting one clears the other so the database constraint is always
satisfied.
"""

from __future__ import annotations

from web.database.model import Coupon

from bp_admin.core import Column, DecimalField, PercentageField, StringField

from .base import CachedModelView


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
            field=PercentageField("percentage"),
        ),
        Column("amount", "Amount", field=DecimalField("amount")),
    ]

    create_fields = [
        StringField("code", required=True),
        DecimalField("amount"),
        PercentageField("percentage"),
    ]

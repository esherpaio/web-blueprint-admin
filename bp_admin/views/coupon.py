from web.database.model import Coupon

from bp_admin.core import (
    CachedModelView,
    Column,
    DecimalField,
    PercentageField,
    StringField,
)


class CouponView(CachedModelView):
    model = Coupon
    name = "Coupon"
    endpoint = "coupons"
    icon = "bi-ticket-perforated"
    order = 50

    can_create = True
    can_delete = True

    columns = [
        Column("code"),
        Column("percentage", field=PercentageField("percentage")),
        Column("amount", field=DecimalField("amount")),
    ]

    create_fields = [
        StringField("code", required=True),
        DecimalField("amount"),
        PercentageField("percentage"),
    ]

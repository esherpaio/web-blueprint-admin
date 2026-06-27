"""Declarative admin views and their registration on the admin blueprint."""

from __future__ import annotations

from bp_admin.core import AdminSite

from .category import CategoryView
from .country import CountryView
from .coupon import CouponView
from .shipment import ShipmentClassView, ShipmentMethodView, ShipmentZoneView
from .user import UserView

admin_site = AdminSite()


def register_views() -> AdminSite:
    """Register every engine view plus manual links to custom pages."""
    admin_site.register(CategoryView)
    admin_site.register(CouponView)
    admin_site.register(UserView)
    admin_site.register(CountryView)
    admin_site.register(ShipmentClassView)
    admin_site.register(ShipmentZoneView)
    admin_site.register(ShipmentMethodView)

    # Manual links to the remaining custom (non-engine) pages.
    admin_site.add_link("Orders", "admin.orders", icon="bi-receipt-cutoff", order=10)
    admin_site.add_link("Products", "admin.products", icon="bi-boxes", order=30)
    admin_site.add_link("Emails", "admin.emails", icon="bi-mailbox", order=60)
    admin_site.add_link(
        "Changelog", "admin.changelog", icon="bi-newspaper", order=10, section="bottom"
    )
    admin_site.add_link(
        "Settings",
        "admin.settings",
        icon="bi-gear-wide-connected",
        order=20,
        section="bottom",
    )
    return admin_site

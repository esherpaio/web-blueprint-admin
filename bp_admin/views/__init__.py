"""Declarative admin views and their registration on the admin blueprint."""

from bp_admin.core import AdminSite

from .category import CategoryView
from .country import CountryView
from .coupon import CouponView
from .settings import SettingsView
from .shipment import ShipmentClassView, ShipmentZoneView
from .user import UserView

admin_site = AdminSite()


def register_views() -> AdminSite:
    admin_site.register(CategoryView)
    admin_site.register(CouponView)
    admin_site.register(UserView)
    admin_site.register(CountryView)
    admin_site.register(ShipmentClassView)
    admin_site.register(ShipmentZoneView)
    admin_site.register(SettingsView)

    # Manual links to the remaining custom (non-engine) pages.
    admin_site.add_link("Orders", "admin.orders", icon="bi-receipt-cutoff", order=10)
    admin_site.add_link("Products", "admin.products", icon="bi-boxes", order=30)
    admin_site.add_link("Emails", "admin.emails", icon="bi-mailbox", order=60)
    admin_site.add_link(
        "Changelog", "admin.changelog", icon="bi-newspaper", order=10, section="bottom"
    )
    return admin_site

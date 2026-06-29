"""Declarative admin views and their registration on the admin blueprint."""

from bp_admin.core import AdminSite

from .category import CategoryView
from .country import CountryView
from .coupon import CouponView
from .order import OrderView
from .product import ProductView
from .settings import SettingsView
from .shipment import ShipmentClassView, ShipmentZoneView
from .user import UserView

admin_site = AdminSite()


def register_views() -> AdminSite:
    admin_site.register(CategoryView)
    admin_site.register(CouponView)
    admin_site.register(OrderView)
    admin_site.register(ProductView)
    admin_site.register(UserView)
    admin_site.register(CountryView)
    admin_site.register(ShipmentClassView)
    admin_site.register(ShipmentZoneView)
    admin_site.register(SettingsView)

    # Manual links to the remaining custom (non-engine) pages.
    admin_site.add_link(
        "Changelog", "admin.changelog", icon="bi-newspaper", order=10, section="bottom"
    )
    return admin_site

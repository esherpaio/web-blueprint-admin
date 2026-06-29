"""Declarative admin views and their registration on the admin blueprint."""

from bp_admin import admin_bp
from bp_admin.core import AdminSite

from .category import CategoryView
from .country import CountryView
from .coupon import CouponView
from .markdown import MarkdownView
from .order import OrderView
from .product import ProductView
from .product_option import ProductOptionView
from .settings import SettingsView
from .shipment import ShipmentClassView, ShipmentZoneView
from .user import UserView

admin_site = AdminSite()

CHANGELOG_URL = (
    "https://raw.githubusercontent.com/esherpaio/web-framework/main/RELEASE.md"
)


def register_views() -> AdminSite:
    admin_site.register(CategoryView)
    admin_site.register(CouponView)
    admin_site.register(OrderView)
    admin_site.register(ProductView)
    admin_site.register(ProductOptionView)
    admin_site.register(UserView)
    admin_site.register(CountryView)
    admin_site.register(ShipmentClassView)
    admin_site.register(ShipmentZoneView)
    admin_site.register(SettingsView)

    # Manual links to the remaining custom (non-engine) pages.
    MarkdownView(
        "changelog", "Changelog", CHANGELOG_URL, icon="bi-newspaper", order=10
    ).register(admin_bp, admin_site)
    return admin_site

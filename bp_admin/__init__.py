from .blueprint import (
    admin_bp,
    admin_static_jobs,
)
from .routes import (
    changelog,
    emails,
    orders,
    products,
    settings,
)
from .views import register_views

# Register the declarative engine views (and their routes) on the blueprint.
register_views().init_blueprint(admin_bp)

__all__ = [
    "admin_bp",
    "admin_static_jobs",
    "changelog",
    "emails",
    "orders",
    "products",
    "register_views",
    "settings",
]

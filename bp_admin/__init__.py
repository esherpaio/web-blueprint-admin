from .blueprint import admin_bp, admin_static_jobs
from .routes import changelog, orders, products
from .views import register_views

register_views().init_blueprint(admin_bp)

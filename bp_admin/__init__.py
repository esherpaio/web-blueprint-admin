from .blueprint import admin_bp, admin_static_jobs
from .routes import orders
from .views import register_views

register_views().init_blueprint(admin_bp)

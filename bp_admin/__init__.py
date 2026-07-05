from .static import admin_static_jobs
from .views import register_views

admin_site = register_views()
admin_bp = admin_site.build_blueprint(import_name=__name__)

import os

from web.automation.task import StaticJob, StaticType
from web.database.model import AppBlueprint
from web.packer.bundle import CssBundle, JsBundle

_dir = os.path.dirname(os.path.abspath(__file__))
admin_static_jobs = [
    StaticJob(
        type_=StaticType.CSS,
        bundles=[CssBundle(os.path.join(_dir, "static", "admin.css"))],
        model=AppBlueprint,
        endpoint="admin",
    ),
    StaticJob(
        type_=StaticType.JS,
        bundles=[JsBundle(os.path.join(_dir, "static"))],
        model=AppBlueprint,
        endpoint="admin",
    ),
]

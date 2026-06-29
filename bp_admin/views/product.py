"""Products list — engine view; detail tabs stay custom routes for now."""

from markupsafe import Markup
from web.database.model import Product

from bp_admin.core import CellFormat, Column, ModelView, StringField


def _view(product_id: int) -> Markup:
    return Markup(
        f'<a class="btn btn-sm btn-secondary" '
        f'href="/admin/products/{product_id}">View</a>'
    )


class ProductView(ModelView):
    model = Product
    name = "Product"
    endpoint = "products"
    icon = "bi-boxes"
    order = 30

    can_create = True
    can_delete = True
    searchable = ["name"]
    order_by = Product.name

    create_fields = [StringField("name")]

    columns = [
        Column("name", "Name"),
        Column("shipment_class.name", "Shipment class"),
        Column("unit_price", "Price", format=CellFormat.PRICE),
        Column("id", "", format=_view, align="end"),
    ]

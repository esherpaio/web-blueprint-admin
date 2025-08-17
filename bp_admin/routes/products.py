from flask import redirect, render_template
from sqlalchemy.orm import joinedload
from web.app.urls import url_for
from web.database import conn
from web.database.model import (
    Product,
    ProductLink,
    ProductMedia,
    ProductOption,
    ProductValue,
    ShipmentClass,
    Sku,
    SkuDetail,
)
from werkzeug import Response

from bp_admin import admin_bp


@admin_bp.get("/admin/products")
def products() -> str:
    with conn.begin() as s:
        products_ = (
            s.query(Product)
            .options(joinedload(Product.shipment_class))
            .filter_by(is_deleted=False)
            .order_by(Product.name)
            .all()
        )
    return render_template(
        "admin/products.html",
        active_menu="products",
        products=products_,
    )


@admin_bp.get("/admin/products/<int:product_id>")
def products_id(product_id: int) -> str | Response:
    with conn.begin() as s:
        product_ = (
            s.query(Product)
            .options(
                joinedload(Product.type_),
                joinedload(Product.shipment_class),
            )
            .filter_by(id=product_id, is_deleted=False)
            .first()
        )
        if not product_:
            return redirect(url_for("admin.products"))
        shipment_classes = (
            s.query(ShipmentClass)
            .filter_by(is_deleted=False)
            .order_by(ShipmentClass.name, ShipmentClass.id)
            .all()
        )
    return render_template(
        "admin/products_id.html",
        active_menu="products",
        product=product_,
        shipment_classes=shipment_classes,
    )


@admin_bp.get("/admin/products/<int:product_id>/options")
def products_id_options(product_id: int) -> str | Response:
    with conn.begin() as s:
        product_ = (
            s.query(Product)
            .options(
                joinedload(Product.type_),
                joinedload(Product.shipment_class),
            )
            .filter_by(id=product_id, is_deleted=False)
            .first()
        )
        if not product_:
            return redirect(url_for("admin.products"))
        product_options = (
            s.query(ProductOption)
            .options(joinedload(ProductOption.values))
            .filter_by(product_id=product_id, is_deleted=False)
            .order_by(ProductOption.order, ProductOption.id)
            .all()
        )
    return render_template(
        "admin/products_id_options.html",
        active_menu="products",
        product=product_,
        product_options=product_options,
    )


@admin_bp.get("/admin/products/<int:product_id>/options/<int:option_id>")
def products_id_options_id(product_id: int, option_id: int) -> str:
    with conn.begin() as s:
        product_ = s.query(Product).filter_by(id=product_id, is_deleted=False).first()
        product_medias = (
            s.query(ProductMedia)
            .options(joinedload(ProductMedia.file_))
            .filter_by(product_id=product_id)
            .order_by(ProductMedia.order, ProductMedia.id)
            .all()
        )
        option = (
            s.query(ProductOption)
            .filter_by(id=option_id, product_id=product_id, is_deleted=False)
            .first()
        )
        option_values = (
            s.query(ProductValue)
            .options(joinedload(ProductValue.media))
            .filter_by(option_id=option_id, is_deleted=False)
            .order_by(ProductValue.order, ProductValue.id)
            .all()
        )
    return render_template(
        "admin/products_id_options_id.html",
        active_menu="products",
        product=product_,
        product_medias=product_medias,
        option=option,
        option_values=option_values,
    )


@admin_bp.get("/admin/products/<int:product_id>/media")
def products_id_media(product_id: int) -> str | Response:
    with conn.begin() as s:
        product_ = (
            s.query(Product)
            .options(
                joinedload(Product.type_),
                joinedload(Product.shipment_class),
            )
            .filter_by(id=product_id, is_deleted=False)
            .first()
        )
        if not product_:
            return redirect(url_for("admin.products"))
        product_medias = (
            s.query(ProductMedia)
            .options(joinedload(ProductMedia.file_))
            .filter_by(product_id=product_id)
            .order_by(ProductMedia.order, ProductMedia.id)
            .all()
        )
    return render_template(
        "admin/products_id_media.html",
        active_menu="products",
        product=product_,
        product_medias=product_medias,
    )


@admin_bp.get("/admin/products/<int:product_id>/links")
def products_id_links(product_id: int) -> str | Response:
    with conn.begin() as s:
        product_ = (
            s.query(Product)
            .options(
                joinedload(Product.type_),
                joinedload(Product.shipment_class),
            )
            .filter_by(id=product_id, is_deleted=False)
            .first()
        )
        if not product_:
            return redirect(url_for("admin.products"))
        product_links = (
            s.query(ProductLink)
            .options(
                joinedload(ProductLink.type_),
                joinedload(ProductLink.sku),
                joinedload(ProductLink.sku, Sku.product),
                joinedload(ProductLink.sku, Sku.details),
                joinedload(ProductLink.sku, Sku.details, SkuDetail.option),
                joinedload(ProductLink.sku, Sku.details, SkuDetail.value),
            )
            .filter_by(product_id=product_.id)
            .order_by(ProductLink.sku_id, ProductLink.type_id)
            .all()
        )
        available_skus = (
            s.query(Sku)
            .options(
                joinedload(Sku.product),
                joinedload(Sku.details),
                joinedload(Sku.details, SkuDetail.option),
                joinedload(Sku.details, SkuDetail.value),
            )
            .filter_by(is_deleted=False)
            .order_by(Sku.slug)
            .all()
        )
    return render_template(
        "admin/products_id_links.html",
        active_menu="products",
        product=product_,
        product_links=product_links,
        available_skus=available_skus,
    )


@admin_bp.get("/admin/products/<int:product_id>/skus")
def products_id_skus(product_id: int) -> str | Response:
    with conn.begin() as s:
        product_ = (
            s.query(Product)
            .options(
                joinedload(Product.type_),
                joinedload(Product.shipment_class),
            )
            .filter_by(id=product_id, is_deleted=False)
            .first()
        )
        if not product_:
            return redirect(url_for("admin.products"))
        skus = (
            s.query(Sku)
            .options(
                joinedload(Sku.details),
                joinedload(Sku.details, SkuDetail.option),
                joinedload(Sku.details, SkuDetail.value),
            )
            .filter_by(product_id=product_.id, is_deleted=False)
            .order_by(Sku.id)
            .all()
        )
    return render_template(
        "admin/products_id_skus.html",
        active_menu="products",
        product=product_,
        skus=skus,
    )

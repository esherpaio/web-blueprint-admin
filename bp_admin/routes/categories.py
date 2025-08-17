from flask import redirect, render_template
from sqlalchemy import false
from sqlalchemy.orm import joinedload
from web.app.urls import url_for
from web.database import conn
from web.database.model import Category, CategoryItem, Sku, SkuDetail
from werkzeug import Response

from bp_admin import admin_bp


@admin_bp.get("/admin/categories")
def categories() -> str:
    with conn.begin() as s:
        categories_ = (
            s.query(Category)
            .filter_by(is_deleted=False)
            .order_by(Category.order, Category.id)
            .all()
        )

    return render_template(
        "admin/categories.html",
        active_menu="categories",
        categories=categories_,
    )


@admin_bp.get("/admin/categories/<int:category_id>")
def categories_id(category_id: int) -> str | Response:
    with conn.begin() as s:
        category_ = s.query(Category).filter_by(id=category_id).first()
        if not category_:
            return redirect(url_for("admin.categories"))

        category_items = (
            s.query(CategoryItem)
            .options(
                joinedload(CategoryItem.sku),
                joinedload(CategoryItem.sku, Sku.product),
                joinedload(CategoryItem.sku, Sku.details),
                joinedload(CategoryItem.sku, Sku.details, SkuDetail.value),
            )
            .filter_by(category_id=category_.id)
            .order_by(CategoryItem.order, CategoryItem.id)
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
            .filter(
                Sku.id.not_in([x.sku.id for x in category_items if x.sku]),
                Sku.is_deleted == false(),
            )
            .order_by(Sku.slug)
            .all()
        )

    return render_template(
        "admin/categories_id.html",
        active_menu="categories",
        category=category_,
        category_items=category_items,
        available_skus=available_skus,
    )

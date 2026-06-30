from typing import Any

from flask import abort, redirect, render_template, request
from psycopg2.errors import ForeignKeyViolation, NotNullViolation, UniqueViolation
from sqlalchemy.exc import IntegrityError
from web.app.urls import url_for
from web.database import conn
from web.error import WebError
from web.i18n import _
from werkzeug import Response

from .db import apply_bulk_edits, delete_objects, resolve_choices
from .enums import Notice, Op
from .pagination import get_pages
from .view import ModelView

WriteError = (WebError, IntegrityError)


def _redirect(endpoint: str, **values: Any) -> Response:
    return redirect(url_for(endpoint, **values))


#
# Notices
#


def error_message(error: Exception) -> str:
    if isinstance(error, WebError):
        if error.translation_key is not None:
            try:
                return _(error.translation_key, **error.translation_kwargs)
            except Exception:
                pass
        return str(error) or "Something went wrong."
    if isinstance(error, IntegrityError):
        orig = getattr(error, "orig", None)
        if isinstance(orig, UniqueViolation):
            return "That value already exists."
        if isinstance(orig, NotNullViolation):
            return "A required value is missing."
        if isinstance(orig, ForeignKeyViolation):
            return "A related record prevents this change."
        return "Could not save due to a database constraint."
    return "Something went wrong."


def notice_text(notice: Notice, view: ModelView) -> str:
    if notice is Notice.CREATED:
        return f"{view.name} created."
    if notice is Notice.DELETED:
        return f"{view.name} deleted."
    if notice is Notice.SAVED:
        return "Changes saved."
    if notice is Notice.DONE:
        return "Action completed."
    return "Something went wrong."


def build_notice(view: ModelView) -> dict[str, str] | None:
    code = request.args.get("saved")
    if not code:
        return None
    try:
        notice = Notice(code)
    except ValueError:
        return None
    level = "danger" if notice is Notice.ERROR else "success"
    return {"text": notice_text(notice, view), "level": level}


#
# Rendering
#


def render_list(
    view: ModelView,
    *,
    error: str | None = None,
    form_values: Any = None,
    create_error: str | None = None,
    create_values: Any = None,
) -> str:
    search = request.args.get("s", type=str, default="")
    page = max(request.args.get("p", type=int, default=1) or 1, 1)
    limit = view.page_size
    offset = (limit * page) - limit
    show_search = bool(search)

    with conn.begin() as s:
        query = view.get_query(s)
        query = view.apply_search(query, search)
        total = query.count()
        query = view.apply_order(query)
        rows = query.limit(limit).offset(offset).all()

        choices = resolve_choices(
            s, [c.field for c in view.columns] + list(view.create_fields)
        )
        pagination = get_pages(offset, limit, total)

        return render_template(
            "admin/_engine/list.html",
            view=view,
            rows=rows,
            total=total,
            pagination=pagination,
            search=search,
            show_search=show_search,
            choices=choices,
            error=error,
            form_values=form_values or {},
            create_error=create_error,
            create_values=create_values or {},
            notice=build_notice(view),
            active_menu=view.endpoint,
        )


def render_detail(
    view: ModelView,
    id_: Any,
    *,
    active_tab: str | None = None,
    error: str | None = None,
    form_values: Any = None,
) -> str:
    with conn.begin() as s:
        obj = view.get_object(s, id_)
        if obj is None:
            abort(404)

        tabs_ctx = [{"tab": tab, "ctx": tab.context(view, s, obj)} for tab in view.tabs]
        action_choices = {
            action.name: resolve_choices(s, action.fields) for action in view.actions
        }
        active = (
            active_tab
            or request.args.get("tab")
            or (view.tabs[0].key if view.tabs else None)
        )

        return render_template(
            "admin/_engine/detail.html",
            view=view,
            obj=obj,
            tabs_ctx=tabs_ctx,
            active_tab=active,
            action_choices=action_choices,
            error=error,
            form_values=form_values or {},
            notice=build_notice(view),
            active_menu=view.endpoint,
        )


#
# List: GET (render) + POST (bulk save / delete)
#


def list_endpoint(view: ModelView) -> str | Response:
    if request.method == "POST":
        try:
            op = Op(request.form.get("_op", ""))
        except ValueError:
            abort(400)
        try:
            with conn.begin() as s:
                if op is Op.DELETE and view.can_delete:
                    delete_objects(
                        s,
                        view.model,
                        request.form.getlist("select"),
                        soft_delete=view.soft_delete,
                        base_query=view.get_query(s),
                    )
                elif op is Op.SAVE:
                    apply_bulk_edits(
                        s,
                        view.model,
                        view.columns,
                        request.form,
                        base_query=view.get_query(s),
                        order_field=view.order_field if view.reorderable else None,
                    )
                else:
                    abort(400)
                view.after_write(s, None)
        except WriteError as error:
            return render_list(
                view, error=error_message(error), form_values=request.form
            )
        saved = Notice.DELETED if op is Op.DELETE else Notice.SAVED
        return _redirect(f"admin.{view.endpoint}", saved=saved)
    return render_list(view)


def create_endpoint(view: ModelView) -> Response | str:
    try:
        with conn.begin() as s:
            view.create(s, request.form, request.files)
    except WriteError as error:
        return render_list(
            view,
            create_error=error_message(error),
            create_values=request.form.to_dict(),
        )
    return _redirect(f"admin.{view.endpoint}", saved=Notice.CREATED)


#
# Detail: GET (render) + tab / action / delete (POST)
#


def singleton_endpoint(view: ModelView) -> Response:
    with conn.begin() as s:
        obj = view.get_query(s).first()
        id_ = obj.id if obj else None
    if id_ is None:
        abort(404)
    return _redirect(f"admin.{view.endpoint}_detail", id_=id_)


def detail_endpoint(view: ModelView, id_: Any) -> str | Response:
    return render_detail(view, id_)


def tab_endpoint(view: ModelView, id_: Any, tab_key: str) -> Response | str:
    tab = view.tab_by_key(tab_key)
    if tab is None:
        abort(404)
    try:
        with conn.begin() as s:
            obj = view.get_object(s, id_)
            if obj is None:
                abort(404)
            tab.handle_post(view, s, obj, request.form, request.files)
    except WriteError as error:
        return render_detail(
            view,
            id_,
            active_tab=tab_key,
            error=error_message(error),
            form_values=request.form,
        )
    return _redirect(
        f"admin.{view.endpoint}_detail", id_=id_, tab=tab_key, saved=Notice.SAVED
    )


def action_endpoint(view: ModelView, id_: Any, name: str) -> Response | str:
    action = view.action_by_name(name)
    if action is None:
        abort(404)
    try:
        with conn.begin() as s:
            obj = view.get_object(s, id_)
            if obj is None:
                abort(404)
            data = action.parse(request.form, request.files)
            action.run(s, obj, data)
            view.after_write(s, obj)
    except WriteError as error:
        return render_detail(view, id_, error=error_message(error))
    return _redirect(f"admin.{view.endpoint}_detail", id_=id_, saved=Notice.DONE)


def delete_endpoint(view: ModelView, id_: Any) -> Response:
    try:
        with conn.begin() as s:
            delete_objects(s, view.model, [id_], soft_delete=view.soft_delete)
            view.after_write(s, None)
    except WriteError:
        return _redirect(f"admin.{view.endpoint}_detail", id_=id_, saved=Notice.ERROR)
    return _redirect(f"admin.{view.endpoint}", saved=Notice.DELETED)

"""User admin view — demonstrates a searchable, bulk-editable list with no
create/delete (users are managed through authentication flows)."""

from typing import Any

from sqlalchemy.orm.session import Session
from web.database.model import Email, Order, User, UserRoleId

from bp_admin.core import (
    BoolField,
    CachedModelView,
    CellFormat,
    Column,
    FormTab,
    InlineTableTab,
    StringField,
)


class UserView(CachedModelView):
    model = User
    name = "User"
    endpoint = "users"
    icon = "bi-people"
    order = 55

    searchable = ["email", "display_name"]
    order_by = [User.id.desc()]
    can_edit = True

    columns = [
        Column("id", "ID"),
        Column("created_at", "Created", format=CellFormat.DATETIME),
        Column("email", "Email"),
        Column("display_name", "Name"),
        Column("role.name", "Role"),
        Column("is_active", "Active", editable=True, field=BoolField("is_active")),
    ]

    tabs = [
        FormTab(
            "General",
            [
                StringField("email"),
                StringField("display_name"),
                BoolField("is_active", readonly=False),
                BoolField("bulk_email", readonly=False),
            ],
        ),
        InlineTableTab(
            "Orders",
            Order,
            "user_id",
            columns=[
                Column("id", "ID"),
                Column("created_at", "Date", format=CellFormat.DATETIME),
                Column("status.name", "Status"),
                Column("total_price", "Total", format=CellFormat.PRICE),
            ],
            can_create=False,
            can_delete=False,
            order_by=Order.created_at.desc(),
            key="orders",
        ),
        InlineTableTab(
            "Emails",
            Email,
            "user_id",
            columns=[
                Column("id", "ID"),
                Column("created_at", "Date", format=CellFormat.DATETIME),
                Column("event_id", "Event"),
                Column("status.name", "Status"),
            ],
            can_create=False,
            can_delete=False,
            order_by=Email.created_at.desc(),
            key="emails",
        ),
    ]

    def get_query(self, s: Session) -> Any:
        return s.query(User).filter(User.role_id != UserRoleId.GUEST)

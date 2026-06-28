"""User admin view — demonstrates a searchable, bulk-editable list with no
create/delete (users are managed through authentication flows)."""

from typing import Any

from sqlalchemy.orm.session import Session
from web.database.model import User

from bp_admin.core import BoolField, Column, FormTab, StringField

from .base import CachedModelView


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
        Column("created_at", "Created", format="datetime"),
        Column("email", "Email"),
        Column("display_name", "Name"),
        Column("role.name", "Role"),
        Column("is_active", "Active", editable=True, field=BoolField("is_active")),
    ]

    tabs = [
        FormTab(
            "General",
            [
                StringField("email", readonly=True),
                StringField("display_name", readonly=True),
                BoolField("is_active"),
                BoolField("bulk_email"),
            ],
        ),
    ]

    def get_query(self, s: Session) -> Any:
        return s.query(User).filter(User.email.is_not(None))

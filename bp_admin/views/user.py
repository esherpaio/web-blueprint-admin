"""User admin view — demonstrates a searchable, bulk-editable list with no
create/delete (users are managed through authentication flows)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm.session import Session
from web.database.model import User

from bp_admin.core import BoolField, Column

from .base import CachedModelView


class UserView(CachedModelView):
    model = User
    name = "User"
    endpoint = "users"
    icon = "bi-people"
    order = 55

    searchable = ["email"]
    order_by = [User.id.desc()]
    can_create = False
    can_delete = False

    columns = [
        Column("id", "ID"),
        Column("email", "Email"),
        Column("display_name", "Name"),
        Column("role.name", "Role"),
        Column("created_at", "Created", format="datetime"),
        Column("is_active", "Active", editable=True, field=BoolField("is_active")),
    ]

    def get_query(self, s: Session) -> Any:
        return s.query(User).filter(User.email.is_not(None))

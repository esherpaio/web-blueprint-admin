"""String-valued enums for the admin engine's decision points.

These are ``StrEnum`` so members compare equal to their string value, which
keeps form/query handling and template comparisons straightforward.
"""

from enum import StrEnum


class Op(StrEnum):
    """Bulk-form operation submitted via the ``_op`` field."""

    SAVE = "save"
    DELETE = "delete"
    ADD = "add"


class Notice(StrEnum):
    """Outcome carried in the ``saved`` query param after a redirect."""

    CREATED = "created"
    SAVED = "saved"
    DELETED = "deleted"
    DONE = "done"
    ERROR = "error"


class InputType(StrEnum):
    """Widget a field renders as."""

    TEXT = "text"
    NUMBER = "number"
    CHECKBOX = "checkbox"
    SELECT = "select"
    TEXTAREA = "textarea"
    ATTRIBUTES = "attributes"
    HTML = "html"
    DATETIME = "datetime"
    HIDDEN = "hidden"


class CellFormat(StrEnum):
    """Display formatter for a read-only column."""

    PRICE = "price"
    DATETIME = "datetime"
    BOOL = "bool"


class AttrType(StrEnum):
    """Value type of a single JSONB attribute row."""

    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    LIST = "list"
    DICT = "dict"


class MenuSection(StrEnum):
    """Sidebar section a menu item belongs to."""

    MAIN = "main"
    BOTTOM = "bottom"
    HIDDEN = "hidden"

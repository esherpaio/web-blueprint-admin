from enum import StrEnum


class Op(StrEnum):
    SAVE = "save"
    DELETE = "delete"
    ADD = "add"


class Notice(StrEnum):
    CREATED = "created"
    SAVED = "saved"
    DELETED = "deleted"
    DONE = "done"
    ERROR = "error"


class InputType(StrEnum):
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
    PRICE = "price"
    DATETIME = "datetime"
    BOOL = "bool"


class AttrType(StrEnum):
    NONE = "none"
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    LIST = "list"
    DICT = "dict"


class MenuSection(StrEnum):
    MAIN = "main"
    BOTTOM = "bottom"
    HIDDEN = "hidden"

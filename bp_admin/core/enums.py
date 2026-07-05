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


class Style(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    DANGER = "danger"
    WARNING = "warning"
    INFO = "info"
    LIGHT = "light"
    DARK = "dark"


class Size(StrEnum):
    SM = "sm"
    LG = "lg"


class Align(StrEnum):
    START = "start"
    CENTER = "center"
    END = "end"


class LinkMode(StrEnum):
    BUTTON = "button"
    TEXT = "text"


class AttrType(StrEnum):
    NONE = "none"
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    LIST = "list"
    DICT = "dict"

    @property
    def label(self) -> str:
        return self.capitalize()


class MenuSection(StrEnum):
    MAIN = "main"
    BOTTOM = "bottom"
    HIDDEN = "hidden"

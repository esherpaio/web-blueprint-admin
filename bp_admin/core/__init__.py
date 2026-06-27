"""Declarative admin engine for the bp_admin blueprint.

Configure pages by subclassing :class:`ModelView` and registering them on an
:class:`AdminSite`. The engine renders Bootstrap 5 list, create and tabbed
detail pages that write straight to the database via SQLAlchemy.
"""

from .action import Action
from .column import Column
from .field import (
    BoolField,
    DateTimeField,
    DecimalField,
    Field,
    FileField,
    HiddenField,
    IntegerField,
    JsonAttributesField,
    SelectField,
    StringField,
    TextAreaField,
)
from .site import AdminSite
from .tab import FormTab, InlineTableTab, Tab, TemplateTab
from .view import Filter, ModelView

__all__ = [
    "Action",
    "AdminSite",
    "BoolField",
    "Column",
    "DateTimeField",
    "DecimalField",
    "Field",
    "FileField",
    "Filter",
    "FormTab",
    "HiddenField",
    "InlineTableTab",
    "IntegerField",
    "JsonAttributesField",
    "ModelView",
    "SelectField",
    "StringField",
    "Tab",
    "TemplateTab",
    "TextAreaField",
]

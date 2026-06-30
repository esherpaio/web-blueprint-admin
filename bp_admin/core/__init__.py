"""Declarative admin engine for the bp_admin blueprint.

Configure pages by subclassing :class:`ModelView` and registering them on an
:class:`AdminSite`. The engine renders Bootstrap 5 list, create and tabbed
detail pages that write straight to the database via SQLAlchemy.
"""

from .action import Action
from .column import Column
from .enums import AttrType, CellFormat, InputType, MenuSection, Notice, Op
from .field import (
    BoolField,
    DateTimeField,
    DecimalField,
    DisplayField,
    Field,
    HiddenField,
    HtmlField,
    IntegerField,
    JsonAttributesField,
    PercentageField,
    SelectField,
    StringField,
    TextAreaField,
)
from .pagination import get_pages
from .site import AdminSite
from .tab import FormTab, InlineTableTab, MediaTab, Tab, TemplateTab
from .view import CachedModelView, Filter, MarkdownView, ModelView, SingletonView

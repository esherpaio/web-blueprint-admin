"""Country admin view — demonstrates foreign-key selects and a detail form with
checkboxes. Countries are reference data, so deletion is disabled."""

from web.database.model import Country, Currency, Region

from bp_admin.core import (
    BoolField,
    CachedModelView,
    Column,
    FormTab,
    SelectField,
    StringField,
)


class CountryView(CachedModelView):
    model = Country
    name = "Country"
    name_plural = "Countries"
    endpoint = "countries"
    icon = "bi-flag"
    order = 65

    searchable = ["name", "code"]
    order_by = [Country.name]
    can_edit = True

    columns = [
        Column("code", "Code"),
        Column("name"),
        Column(
            "allows_shipping",
            "Shipping",
            editable=True,
            field=BoolField("allows_shipping"),
        ),
    ]

    create_fields = [
        StringField("name", required=True),
        StringField("code", required=True),
        SelectField.from_model("currency_id", Currency, label_attr="code"),
        SelectField.from_model("region_id", Region, label_attr="name"),
    ]

    tabs = [
        FormTab(
            "General",
            [
                StringField("name", required=True),
                StringField("code", required=True),
                SelectField.from_model("currency_id", Currency, label_attr="code"),
                SelectField.from_model("region_id", Region, label_attr="name"),
                BoolField("requires_billing_state", readonly=False),
                BoolField("requires_billing_vat", readonly=False),
                BoolField("allows_shipping", readonly=False),
            ],
        ),
    ]

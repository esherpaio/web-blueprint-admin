from typing import Iterable

from sqlalchemy.orm.session import Session

from ..enums import InputType
from ..field import Field


def resolve_choices(s: Session, fields: Iterable[Field]) -> dict[str, list]:
    choices: dict[str, list] = {}
    for field in fields:
        if field.input_type in (InputType.SELECT, InputType.MULTISELECT):
            choices[field.name] = field.choices(s)
    return choices

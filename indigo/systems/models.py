import typing as t
from dataclasses import dataclass

from indigo.database.models import DatabaseRecord

AskDefinition = str


@dataclass
class Argument:
    name: str
    type_: t.Type
    is_optional: bool


@dataclass
class Ask:
    definition: AskDefinition
    method_name: str
    arguments: t.Sequence[Argument]

    @property
    def has_database_arguments(self) -> bool:
        return any(
            [issubclass(a.type_, DatabaseRecord) for a in self.arguments]
        )

import abc
import typing as t
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    GetCoreSchemaHandler,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_core import core_schema

__all__ = [
    "ID",
    "Model",
    "Field",
    "model_validator",
    "field_validator",
    "ValidationError",
    "Error",
]


class ID(str):
    def __new__(cls, value: t.Optional[str] = None) -> "ID":
        if value:
            # Validation
            UUID(value)
            id_ = value
        else:
            id_ = str(uuid4())
        return t.cast("ID", id_)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: t.Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls, handler(str)
        )


class Model(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_default=True,
        validate_assignment=True,
    )


class Error(Exception, abc.ABC): ...

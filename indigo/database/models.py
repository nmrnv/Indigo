import typing as t
import uuid
from abc import ABC
from datetime import datetime
from pathlib import Path

from indigo.models.base import (
    ID,
    Error,
    Field,
    Model,
    field_validator,
    model_validator,
)
from indigo.utils import date_utils, hash_utils


class DatabaseRecord(Model, ABC):
    id_: ID = Field(
        default_factory=ID,
        alias="_id",
        frozen=True,
    )

    def __hash__(self):
        return hash(self.id_)

    @field_validator("id_")
    def validate_id(cls, value) -> ID:
        try:
            uuid.UUID(value)
        except ValueError:
            raise ValueError("Invalid ID {value!r}.")
        return value


DatabaseRecord_ = t.TypeVar("DatabaseRecord_", bound=DatabaseRecord)


class DeterministicDatabaseRecord(DatabaseRecord, ABC):
    DETERMINANT_FIELDS: t.ClassVar[t.Sequence[str]]
    _ALLOWED_FIELD_TYPES: t.ClassVar[t.Tuple[t.Type, ...]] = (
        int,
        float,
        str,
        bool,
        datetime,
        Path,
    )
    # Overriding default behaviour
    id_: ID = Field(
        default=None,  # type: ignore
        alias="_id",
        frozen=True,
    )

    def __init_subclass__(cls):
        if not cls.DETERMINANT_FIELDS:
            raise ValueError(
                "DeterministicDatabaseRecord must define "
                "at least one determinant field."
            )
        for field in cls.DETERMINANT_FIELDS:
            if field not in cls.__annotations__:
                raise ValueError(
                    f"Determinant field {field!r} is not defined in"
                    f" {cls.__name__}."
                )
            if (
                field_type := cls.__annotations__[field]
            ) and not issubclass(field_type, cls._ALLOWED_FIELD_TYPES):
                raise ValueError(
                    f"Determinant field {field!r}'s type is not allowed for"
                    " a determinant field."
                )

    @model_validator(mode="before")
    def validate_raw(cls, values):
        cls = t.cast(t.Type, cls)
        if "_id" not in values:
            determinant_values = [cls.__name__]
            for determinant_field in cls.DETERMINANT_FIELDS:
                value = values.get(
                    cls.__fields__[determinant_field].alias
                    or determinant_field
                )
                if not value:
                    continue
                if isinstance(value, (int, float, bool, str)):
                    determinant_values.append(str(value))
                elif isinstance(value, datetime):
                    date_str = date_utils.date_str(value, worded=False)
                    determinant_values.append(date_str)
                elif isinstance(value, Path):
                    determinant_values.append(value.as_posix())
            if len(determinant_values) < 2:
                raise ValueError(
                    "Cannot generate id based only on the class name."
                )
            identifier = "_".join(determinant_values)
            values["_id"] = hash_utils.generate_uuid(identifier)
        return values

    @field_validator("id_")  # Overriding default behaviour
    def validate_id(cls, value) -> ID:
        try:
            uuid.UUID(value)
        except ValueError:
            raise ValueError("UUID id expected.")
        return value


class Hideable(Model):
    hidden: bool = False

    @property
    def is_hidden(self) -> bool:
        return self.hidden

    def hide(self):
        self.hidden = True

    def unhide(self):
        self.hidden = False


class MetadataRecord(DatabaseRecord):
    key: str  # Class attribute

    def __init__(self, *args, **kwargs):
        if "_id" not in kwargs:
            kwargs["_id"] = self.__class__.key
        super().__init__(*args, **kwargs)

    def __init_subclass__(cls, *args, **kwargs):
        cls.key = ID(hash_utils.generate_uuid(cls.__name__))
        super().__init_subclass__(*args, **kwargs)

    def dict(self, *args, **kwargs):
        class_ = self.__class__
        return {
            "_id": class_.__name__,
            "type": class_.__module__ + "." + class_.__name__,
            **super().model_dump(*args, by_alias=True, **kwargs),
        }


MetadataRecord_ = t.TypeVar("MetadataRecord_", bound=MetadataRecord)


class StorageError(Error): ...


class DatabaseError(Error): ...


class TableNotFoundError(DatabaseError): ...

import typing as t
from datetime import datetime
from pathlib import Path

import pytest
from freezegun import freeze_time

from indigo.base import ID, ValidationError
from indigo.database.models import (
    DatabaseRecord,
    DeterministicDatabaseRecord,
)
from indigo.utils import date_utils


def test_database_record_id_validation():
    assert DatabaseRecord()
    assert DatabaseRecord(_id=ID())


@pytest.mark.parametrize(
    "invalid_value",
    [1, 2.0, "str", b"str", True],
)
def test_database_record_id_validation_failure(invalid_value):
    # Then
    with pytest.raises(ValidationError):
        # When
        DatabaseRecord(_id=invalid_value)

    # Then
    with pytest.raises(ValidationError):
        # When
        DatabaseRecord().id_ = invalid_value


@freeze_time("22/02/2022")
@pytest.mark.parametrize("test_field_index", list(range(6)))
def test_deterministic_database_record(test_field_index: int):
    # Given
    class TestClass(DeterministicDatabaseRecord):
        DETERMINANT_FIELDS = [
            "int_p",
            "float_p",
            "bool_p",
            "str_p",
            "datetime_p",
            "path_p",
        ]

        int_p: int
        float_p: float
        bool_p: bool
        str_p: str
        datetime_p: datetime
        path_p: Path

    # When
    test_object = TestClass(
        int_p=1,
        float_p=1.1,
        bool_p=True,
        str_p="a",
        datetime_p=date_utils.zeroed_datetime(),
        path_p=Path.home(),
    )
    duplicate_object = TestClass(
        int_p=1,
        float_p=1.1,
        bool_p=True,
        str_p="a",
        datetime_p=date_utils.zeroed_datetime(),
        path_p=Path.home(),
    )
    differing_object = TestClass(
        int_p=2 if test_field_index == 0 else 1,
        float_p=2.1 if test_field_index == 1 else 1.1,
        bool_p=False if test_field_index == 2 else True,
        str_p="b" if test_field_index == 3 else "a",
        datetime_p=(
            date_utils.yesterday()
            if test_field_index == 4
            else date_utils.zeroed_datetime()
        ),
        path_p=Path.cwd() if test_field_index == 5 else Path.home(),
    )

    # Then
    assert test_object == duplicate_object
    assert test_object.id_ == duplicate_object.id_
    assert test_object != differing_object
    assert test_object.id_ != differing_object


def test_deterministic_database_record_with_optional_fields():
    # Given
    class TestClass(DeterministicDatabaseRecord):
        DETERMINANT_FIELDS = ["int_p", "float_p"]

        int_p: int
        float_p: t.Optional[float] = None

    # When
    test_object = TestClass(int_p=1)
    duplicate_object = TestClass(int_p=1)

    # Then
    assert test_object == duplicate_object
    assert test_object.id_ == duplicate_object.id_


def test_deterministic_database_record_empty_determinants():
    # Then
    with pytest.raises(
        ValueError,
        match=(
            "DeterministicDatabaseRecord must define at least one"
            " determinant field"
        ),
    ):
        # When
        class _(DeterministicDatabaseRecord):
            DETERMINANT_FIELDS = []
            int_p: int


def test_deterministic_database_records_undefined_field():
    # Then
    with pytest.raises(
        ValueError,
        match="Determinant field 'undefined' is not defined in _.",
    ):
        # When
        class _(DeterministicDatabaseRecord):
            DETERMINANT_FIELDS = ["undefined"]
            int_p: int


def test_deterministic_database_record_unsupported_type():
    # Then
    with pytest.raises(
        ValueError,
        match=(
            "Determinant field 'unsupported''s type "
            "is not allowed for a determinant field."
        ),
    ):
        # When
        class _(DeterministicDatabaseRecord):
            DETERMINANT_FIELDS = ["unsupported"]
            unsupported: bytes


def test_deterministic_database_record_no_values():
    # Given
    class TestClass(DeterministicDatabaseRecord):
        DETERMINANT_FIELDS = ["int_p"]
        int_p: t.Optional[int]

    # When
    with pytest.raises(ValidationError) as error:
        TestClass(int_p=None)

    # Then
    assert "Cannot generate id based only on the class name." in str(
        error.value.errors()[0]["msg"]
    )


def test_deterministic_database_record_invalid_id():
    # Given
    class TestClass(DeterministicDatabaseRecord):
        DETERMINANT_FIELDS = ["int_p"]
        int_p: int

    # Then
    with pytest.raises(
        ValueError, match="badly formed hexadecimal UUID string"
    ):
        # When
        TestClass(_id=ID("invalid_uuid"), int_p=1)

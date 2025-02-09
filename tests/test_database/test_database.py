import pytest

from indigo.base import ID
from indigo.database.database import Database
from indigo.database.models import DatabaseError, MetadataRecord
from tests.conftest import DatabaseRecordStub


class MetadataRecordStub(MetadataRecord):
    field: str


class NonDatabaseRecord:
    pass


def test_initialisation(database: Database):
    # Then
    assert database.database is not None
    assert database.metadata is not None
    assert database.name == "TestSystemDatabase"


def test_count(database: Database):
    # When
    database.save(DatabaseRecordStub())

    # Then
    assert database.count(DatabaseRecordStub) == 1

    # When
    database.save(DatabaseRecordStub())

    # Then
    assert database.count(DatabaseRecordStub) == 2


def test_exists(database: Database):
    # Given
    record = DatabaseRecordStub()
    # The following line also tests exists with non-existing tables
    assert not database.exists(DatabaseRecordStub, record.id_)

    # When
    database.save(record)

    # Then
    assert database.exists(DatabaseRecordStub, record.id_)

    # When
    database.delete(DatabaseRecordStub, record.id_)

    # Then
    assert not database.exists(DatabaseRecordStub, record.id_)


def test_save(database: Database):
    # Given
    record = DatabaseRecordStub()

    # When
    database.save(record)
    retrieved_record = database.retrieve(DatabaseRecordStub, record.id_)

    # Then
    assert retrieved_record == record


@pytest.mark.parametrize(
    "invalid_record",
    [1, 2.0, "3", b"4", True, None, lambda x: x, NonDatabaseRecord()],
)
def test_save_failures(database: Database, invalid_record):
    # Then
    with pytest.raises(DatabaseError):
        # When
        database.save(invalid_record)  # type: ignore


def test_save_failure_if_already_exists(database: Database):
    # Given
    record = DatabaseRecordStub()
    database.save(record)

    # Then
    with pytest.raises(DatabaseError):
        # When
        database.save(record)


def test_update(database: Database):
    # Given
    record = DatabaseRecordStub()
    database.save(record)
    assert record.bool_p

    # When
    record.bool_p = False
    database.update(record)
    updated_record = database.retrieve(DatabaseRecordStub, record.id_)

    # Then
    if not updated_record:
        pytest.fail("Could not retrieve test record.")
    assert not updated_record.bool_p


@pytest.mark.parametrize(
    "invalid_record",
    [1, 2.0, "3", b"4", True, None, lambda x: x, NonDatabaseRecord()],
)
def test_update_failures_with_non_supported_class(
    database: Database, invalid_record
):
    # Then
    with pytest.raises(DatabaseError):
        # When
        database.update(invalid_record)  # type: ignore


def test_update_fails_with_non_existing_record(database: Database):
    # Given
    record_ = DatabaseRecordStub()
    database.save(record_)  # To create the table

    random_uuid = ID()
    record = DatabaseRecordStub(_id=random_uuid)
    assert not database.exists(DatabaseRecordStub, random_uuid)

    # Then
    with pytest.raises(DatabaseError) as e:
        # When
        database.update(record)
    assert e.type == DatabaseError


def test_retrieve(database: Database):
    # Given
    record = DatabaseRecordStub()
    # The following line also tests retrieve with non-existing tables
    assert not database.retrieve(DatabaseRecordStub, record.id_)

    # When
    database.save(record)
    retrieved_record = database.retrieve(DatabaseRecordStub, record.id_)

    # Then
    assert retrieved_record == record
    assert not database.retrieve(DatabaseRecordStub, "invalid_key")


def test_list(database: Database):
    # Given
    record_one = DatabaseRecordStub()
    record_two = DatabaseRecordStub()
    assert database.list(DatabaseRecordStub) == []
    database.save(record_one)

    # When
    records = database.list(DatabaseRecordStub)

    # Then
    assert records == [record_one]

    # When
    database.save(record_two)
    records = database.list(DatabaseRecordStub)

    # Then
    assert records == [record_one, record_two]


def test_list_with_predicate(database: Database):
    # Given
    record_one = DatabaseRecordStub(bool_p=True)
    record_two = DatabaseRecordStub(bool_p=False)

    # When
    database.save(record_one)
    database.save(record_two)
    records = database.list(
        cls=DatabaseRecordStub, predicate=lambda x: x.bool_p
    )

    # Then
    assert records == [record_one]


def test_delete(database: Database):
    # Given
    record = DatabaseRecordStub()

    # When
    database.save(record)

    # Then
    assert database.exists(DatabaseRecordStub, record.id_)

    # When
    database.delete(DatabaseRecordStub, record.id_)

    # Then
    assert not database.exists(DatabaseRecordStub, record.id_)


def test_delete_failure(database: Database):
    # Given
    invalid_record = DatabaseRecordStub()

    # Then
    with pytest.raises(DatabaseError):
        # When
        database.delete(DatabaseRecordStub, invalid_record.id_)


def test_save_update_delete(database: Database):
    # Given
    updated_record = DatabaseRecordStub()
    database.save(updated_record)
    deleted_record = DatabaseRecordStub()
    database.save(deleted_record)
    unchanged_record = DatabaseRecordStub()
    database.save(unchanged_record)

    saved_record = DatabaseRecordStub()
    updated_record.bool_p = not unchanged_record.bool_p

    # When
    saved, updated, deleted, unchanged = database.save_update_delete(
        cls=DatabaseRecordStub,
        items=[saved_record, updated_record, unchanged_record],
    )

    # Then
    assert saved == [saved_record]
    assert updated == [updated_record]
    assert deleted == [deleted_record]
    assert unchanged == [unchanged_record]


def test_meta(database: Database):
    # Given
    assert not database.meta_exists(MetadataRecordStub)

    # When
    metadata = MetadataRecordStub(field="value")
    database.meta_set(metadata)

    # Then
    assert database.meta_exists(MetadataRecordStub)
    assert database.meta_retrieve(MetadataRecordStub) == metadata

    # When
    database.meta_delete(MetadataRecordStub)

    # Then
    assert not database.meta_exists(MetadataRecordStub)
    assert not database.meta_retrieve(MetadataRecordStub)


@pytest.mark.parametrize(
    "invalid_record",
    [1, 1.0, True, b"", None, lambda x: x, NonDatabaseRecord()],
)
def test_meta_set_failures(database: Database, invalid_record):
    # Then
    with pytest.raises(
        DatabaseError,
        match="Only subclasses of MetadataRecord can be saved as metadata.",
    ):
        # When
        database.meta_set(invalid_record)  # type: ignore

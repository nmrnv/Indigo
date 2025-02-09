import typing as t

import pytest

from indigo.models.base import ID
from indigo.systems.system import System, SystemError_
from indigo.tools.linker import Linker
from tests.conftest import DatabaseRecordStub


def make_record(
    system: System, id_: t.Optional[ID] = None
) -> DatabaseRecordStub:
    id_ = id_ or ID()
    record = DatabaseRecordStub(_id=id_)
    system.database.save(record)
    return record


def test_database_record_annotation():
    # Given
    class TestSystem(System):
        @System.ask("method")
        def _method(self, parameter: DatabaseRecordStub):
            self.argument = parameter

    system = TestSystem()
    record = make_record(system)
    Linker.link(DatabaseRecordStub, [record.id_])

    # When
    system._handle_ask("method 1")

    # Then
    assert system.argument == record
    del System.asks["TestSystem"]  # type: ignore
    Linker.unlink()


def test_database_record_optional_annotation():
    # Given
    class TestSystem(System):
        @System.ask("method")
        def _method(
            self,
            parameter_1: t.Optional[DatabaseRecordStub] = None,
            parameter_2: t.Optional[DatabaseRecordStub] = None,
        ):
            self.argument_1 = parameter_1
            self.argument_2 = parameter_2

    system = TestSystem()
    record_1 = make_record(system)
    record_2 = make_record(system)
    Linker.link(DatabaseRecordStub, [record_1.id_, record_2.id_])

    # When
    system._handle_ask("method 2")

    # Then
    assert system.argument_1 == record_2
    assert not system.argument_2

    # When
    system._handle_ask("method 1 2")

    # Then
    assert system.argument_1 == record_1
    assert system.argument_2 == record_2

    del System.asks["TestSystem"]  # type: ignore
    Linker.unlink()


def test_database_record_is_not_linked(typer_mock):
    # Given
    class TestSystem(System):
        @System.ask("method")
        def _method(self, parameter: DatabaseRecordStub):
            self.argument = parameter

    system = TestSystem()

    # When
    system._handle_ask("method 1")

    # Then
    assert not hasattr(system, "argument")
    typer_mock.header.assert_called_once_with(
        "No linked ids. List objects to link."
    )
    del System.asks["TestSystem"]  # type: ignore


def test_database_record_does_not_exist():
    # Given
    class TestSystem(System):
        @System.ask("method")
        def _method(self, parameter: DatabaseRecordStub):
            self.argument = parameter

    system = TestSystem()
    record = make_record(system)
    Linker.link(DatabaseRecordStub, [record.id_])
    system.database.delete(DatabaseRecordStub, record.id_)

    # Then
    with pytest.raises(
        SystemError_,
        match=f"DatabaseRecordStub with id {record.id_!r} not found.",
    ):
        # When
        assert not hasattr(system, "argument")
        system._handle_ask("method 1")

    del System.asks["TestSystem"]  # type: ignore

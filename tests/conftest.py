import typing as t
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import freezegun
import pytest

from indigo.base import Field
from indigo.config import Config
from indigo.database.database import Database
from indigo.database.models import (
    DatabaseRecord,
    DeterministicDatabaseRecord,
)
from indigo.database.mongodb import make_client
from indigo.systems.system import System
from indigo.tools.linker import Linker
from indigo.tools.typer import Typer
from indigo.utils import date_utils


@pytest.fixture(autouse=True)
def config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    data_directory = tmp_path / ".indigo.debug"
    monkeypatch.setenv("INDIGO_DEBUG_DIRECTORY", data_directory.as_posix())
    monkeypatch.setenv("INDIGO_DATABASE_USERNAME", "mongodb")
    monkeypatch.setenv("INDIGO_DATABASE_PASSWORD", "password")
    Config.make(debug=True)


@pytest.fixture
def make_directories():
    router = Config.router
    root_directory = router.root_directory
    (root_directory / "notes").mkdir()
    (root_directory / "purpose").mkdir()
    (root_directory / "purpose" / "essays").mkdir()
    (root_directory / "thoughts").mkdir()


@pytest.fixture(autouse=True)
def patch_database(monkeypatch: pytest.MonkeyPatch):
    mongo_client = make_client()
    test_database_name = "TestSystemDatabase"
    real_init = Database.__init__

    def patched_init(self, *_, **__):
        real_init(self, test_database_name)

    monkeypatch.setattr(Database, "__init__", patched_init)
    yield
    mongo_client.drop_database(test_database_name)


@pytest.fixture
def database():
    test_database_name = "TestSystemDatabase"
    yield Database(name=test_database_name)


class DatabaseRecordStub(DatabaseRecord):
    int_p: int = 1
    float_p: float = 1.1
    str_p: str = "str"
    bool_p: bool = True
    datetime_p: datetime = Field(default_factory=date_utils.now)


@pytest.fixture
def system():
    class TestSystem(System):
        def _on_start(self):
            pass

        @System.ask("ask")
        def test_ask(self, argument: str):
            return argument

        @System.ask("optional ask")
        def test_optional_ask(
            self, argument: str, optional_argument: t.Optional[str] = None
        ):
            return argument, optional_argument

    yield TestSystem()
    System.asks["TestSystem"] = {}


@pytest.fixture(autouse=True)
def unlink_linker():
    Linker.unlink()


@pytest.fixture
def disable_linker():
    resolve = Linker.resolve
    Linker.resolve = lambda x, _: x  # type: ignore
    yield Linker
    Linker.resolve = resolve


@pytest.fixture
def typer_mock(monkeypatch: pytest.MonkeyPatch):
    mock = MagicMock()
    monkeypatch.setattr("indigo.systems.system.Typer", mock)
    return mock


@pytest.fixture(autouse=True, scope="session")
def typer_clear_patch():
    Typer.clear = lambda: None


class FileMock:
    unique_counter = 26

    @property
    def file_tag(self) -> str:
        file_tag = ""
        self.__class__.unique_counter += 1
        integer = self.__class__.unique_counter
        while integer > 0:
            integer, remainder = divmod(integer - 1, 26)
            file_tag = chr(ord("a") + remainder) + file_tag
        return f"{file_tag}_file"

    def __init__(self, path: Path):
        self.path = path
        if not self.path.exists():
            self.path.touch()

    def write(self, *lines):
        self.path.write_text("\n".join(lines))


@pytest.fixture
def test_file(tmp_path: Path) -> FileMock:
    return FileMock(tmp_path / "test_file.md")


@pytest.fixture
def frozen_time():
    with freezegun.freeze_time("2022-11-13") as frozen_time:
        yield frozen_time


@pytest.fixture(autouse=True, scope="session")
def freezegun_datetime_patch():
    DeterministicDatabaseRecord._ALLOWED_DETERMINANT_FIELD_TYPES.extend(
        [
            freezegun.api.FakeDatetime,
            t.Optional[freezegun.api.FakeDatetime],
        ]
    )

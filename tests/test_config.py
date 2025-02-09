import os
from pathlib import Path

import pytest

from indigo.config import (
    Config,
    ConfigError,
    Environment,
    get_directory,
)


@pytest.fixture
def provide_env_variables(monkeypatch, tmp_path: Path):
    monkeypatch.setenv(
        Environment.DATA_DIRECTORY, (tmp_path / ".indigo").as_posix()
    )
    monkeypatch.setenv(
        Environment.DEBUG_DIRECTORY,
        (tmp_path / ".indigo.debug").as_posix(),
    )
    monkeypatch.setenv(
        Environment.NOTES_DIRECTORY, (tmp_path / "notes").as_posix()
    )
    monkeypatch.setenv(Environment.DATABASE_USERNAME, "db-username")
    monkeypatch.setenv(Environment.DATABASE_PASSWORD, "db-password")
    monkeypatch.setenv(Environment.AWS_ACCESS_KEY_ID, "aws-key")
    monkeypatch.setenv(Environment.AWS_ACCESS_KEY_SECRET, "aws-secret")
    monkeypatch.setenv(Environment.ENCRYPTION_KEY, "encryption-key")


def test_environment_get_value(monkeypatch):
    # Given
    monkeypatch.setenv("INDIGO_DATA_DIRECTORY", "value")

    # Then
    assert Environment.DATA_DIRECTORY.is_provided()
    assert Environment.DATA_DIRECTORY.get_value() == "value"


def test_environment_not_provided_value():
    # Given
    # Removing as we need to simulate when it is not provided
    del os.environ["INDIGO_DATA_DIRECTORY"]
    assert "INDIGO_DATA_DIRECTORY" not in os.environ

    # Then
    assert not Environment.DATA_DIRECTORY.is_provided()
    with pytest.raises(
        ConfigError,
        match=(
            "ConfigError: Environment.DATA_DIRECTORY environment variable"
            " not provided"
        ),
    ):
        Environment.DATA_DIRECTORY.get_value()


def test_get_directory_existing(tmp_path: Path):
    # Given
    directory_path = tmp_path / "directory"
    directory_path.mkdir()
    filepath = directory_path / "file"
    filepath.touch()

    # Then
    assert get_directory(directory_path) == directory_path
    assert filepath.exists()


def test_get_directory_not_existing_created(tmp_path: Path):
    # Given
    directory_path = tmp_path / "directory"
    assert not directory_path.exists()

    # Then
    assert get_directory(directory_path) == directory_path
    assert directory_path.is_dir()


def test_get_directory_non_directory(tmp_path: Path):
    # Given
    directory_path = tmp_path / "directory"
    directory_path.touch()
    assert not directory_path.is_dir()

    # Then
    with pytest.raises(
        ConfigError,
        match=(
            f"ConfigError: {directory_path.as_posix()!r} must be a"
            " directory"
        ),
    ):
        # When
        get_directory(directory_path)


def test_singleton_config_init_failure():
    # Then
    with pytest.raises(ConfigError):
        # When
        Config()


@pytest.mark.parametrize(
    "debug, directory",
    [(False, ".indigo"), (True, ".indigo.debug")],
)
@pytest.mark.usefixtures("make_directories", "provide_env_variables")
def test_make(debug: bool, directory: str, tmp_path: Path):
    # When
    Config.make(debug=debug)

    # Then
    assert Config.debug == debug
    assert Config.encryption_key == b"encryption-key"

    # Then assert Router paths
    expected_root_path = tmp_path / directory
    assert Config.router.root_directory == expected_root_path

    expected_notes_directory = (
        tmp_path / "notes" if not debug else expected_root_path / "notes"
    )
    assert Config.router.notes_directory == expected_notes_directory

    # Then assert Database Config
    assert Config.database_config.username == "db-username"
    assert Config.database_config.password == "db-password"
    assert (
        Config.database_config.directory == expected_root_path / "mongodb"
    )

    # Then assert AWS Config
    assert Config.aws_config.access_key_id == "aws-key"
    assert Config.aws_config.access_key_secret == "aws-secret"
    assert Config.aws_config.region == "eu-west-2"
    assert Config.aws_config.bucket == "indigo"


def test_make_debug_with_no_debug_directory_provided(
    tmp_path: Path, provide_env_variables, monkeypatch
):
    # Given
    monkeypatch.delenv("INDIGO_DEBUG_DIRECTORY")

    # When
    Config.make(debug=True)

    # Then
    assert (
        Config.router.root_directory
        == Path(__file__).parent.parent / ".indigo.debug"
    )

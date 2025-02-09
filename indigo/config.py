import os
from enum import Enum
from pathlib import Path

from indigo.base import Error

__all__ = ["Config"]


class Environment(str, Enum):
    DATA_DIRECTORY = "INDIGO_DATA_DIRECTORY"
    DEBUG_DIRECTORY = "INDIGO_DEBUG_DIRECTORY"
    NOTES_DIRECTORY = "INDIGO_NOTES_DIRECTORY"
    DATABASE_USERNAME = "INDIGO_DATABASE_USERNAME"
    DATABASE_PASSWORD = "INDIGO_DATABASE_PASSWORD"
    AWS_ACCESS_KEY_ID = "INDIGO_AWS_ACCESS_KEY_ID"
    AWS_ACCESS_KEY_SECRET = "INDIGO_AWS_ACCESS_KEY_SECRET"
    ENCRYPTION_KEY = "INDIGO_ENCRYPTION_KEY"

    def get_value(self) -> str:
        if not (value := os.getenv(self)):
            raise ConfigError(
                f"ConfigError: {self} environment variable not provided"
            )
        return value

    def is_provided(self) -> bool:
        return self in os.environ


class ConfigError(Error): ...


def get_directory(directory: Path) -> Path:
    if not directory.exists():
        directory.mkdir(parents=True)
    elif not directory.is_dir():
        raise ConfigError(
            f"ConfigError: {directory.as_posix()!r} must be a directory."
        )
    return directory


class DatabaseConfig:
    username: str
    password: str
    directory: Path

    def __init__(self):
        self.username = Environment.DATABASE_USERNAME.get_value()
        self.password = Environment.DATABASE_PASSWORD.get_value()
        self.directory = get_directory(
            Config.router.root_directory / "mongodb"
        )


class AWSConfig:
    access_key_id: str
    access_key_secret: str
    region: str = "eu-west-2"
    bucket: str = "indigo"

    def __init__(self):
        self.access_key_id = Environment.AWS_ACCESS_KEY_ID.get_value()
        self.access_key_secret = (
            Environment.AWS_ACCESS_KEY_SECRET.get_value()
        )


class Router:
    @property
    def root_directory(self) -> Path:
        if not Config.debug:
            return get_directory(
                Path(Environment.DATA_DIRECTORY.get_value())
            )
        return get_directory(
            Path(Environment.DEBUG_DIRECTORY.get_value())
            if Environment.DEBUG_DIRECTORY.is_provided()
            else Path(__file__).parent.parent / ".indigo.debug"
        )

    @property
    def notes_directory(self) -> Path:
        return get_directory(
            Path(Environment.NOTES_DIRECTORY.get_value())
            if not Config.debug
            else self.root_directory / "notes"
        )

    @property
    def file_errors_log(self) -> Path:
        return self.root_directory / "file_errors.log"

    @property
    def purpose_directory(self) -> Path:
        return get_directory(self.notes_directory / "purpose")

    @property
    def essays_directory(self) -> Path:
        return get_directory(self.notes_directory / "purpose" / "essays")

    @property
    def thoughts_directory(self) -> Path:
        return get_directory(self.notes_directory / "thoughts")

    @property
    def studies_directory(self) -> Path:
        return get_directory(self.notes_directory / "studies")

    @property
    def words_directory(self) -> Path:
        return get_directory(self.notes_directory / "languages" / "words")

    @property
    def archive_directory(self) -> Path:
        return get_directory(self.notes_directory / "archive")


class Config:
    debug: bool
    encryption_key: bytes

    router: Router
    database_config: DatabaseConfig
    aws_config: AWSConfig

    def __init__(self):
        raise ConfigError("ConfigError: Config is a singleton.")

    @classmethod
    def make(cls, *, debug: bool):
        cls.debug = debug
        cls.encryption_key = Environment.ENCRYPTION_KEY.get_value().encode(
            "utf8"
        )

        cls.router = Router()
        cls.database_config = DatabaseConfig()
        cls.aws_config = AWSConfig()

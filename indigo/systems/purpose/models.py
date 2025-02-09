import os
import typing as t
from datetime import datetime
from pathlib import Path

from librum.files import File, FileError

from indigo.base import ID, Error
from indigo.database.models import (
    DeterministicDatabaseRecord,
    Field,
)
from indigo.utils import date_utils

Tag = str
Tasks = t.Dict[str, t.Tuple[bool, t.Optional["Tasks"]]]
WordDefinition = WordMeaning = WordUsage = str


class FileRecord(DeterministicDatabaseRecord):
    DETERMINANT_FIELDS = ["path"]

    path: Path
    file_tag: str
    created_at: datetime
    updated_at: datetime

    title: str
    tags: t.Sequence[Tag] = Field(default=[])

    def __init__(self, *args, **kwargs):
        stats = os.stat(str(kwargs["path"]))
        kwargs["created_at"] = date_utils.from_timestamp(stats.st_ctime)
        kwargs["updated_at"] = date_utils.from_timestamp(stats.st_mtime)
        super().__init__(*args, **kwargs)

    def __eq__(self, other) -> bool:
        return self.id_ == other.id_ and self.updated_at == other.updated_at

    def model_dump(self, *args, **kwargs) -> dict:
        # When creating a dictionary, we are replacing
        # the Path object with a Str one because
        # BSON, hence MongoDB, cannot encode Paths
        dictionary = super().model_dump(*args, **kwargs)
        dictionary["path"] = self.path.as_posix()
        return dictionary


class DirectoryError(Error): ...


class Directory:
    location: Path
    subdirectories: t.Set[Path]
    files: t.Set[File]
    file_records: t.Set[FileRecord]
    file_tags: t.Set[Tag]
    errors: t.List[str]
    is_parsed: bool = False

    def __init__(self, location: Path):
        self.location = location
        if not location.is_dir():
            raise DirectoryError(
                "Cannot initialise Directory."
                "Location path is not a directory."
            )

        self.files = set()
        self.subdirectories = set()
        self.file_records = set()
        self.file_tags = set()
        self.errors = []

        for path in location.iterdir():
            if path.is_dir():
                self.subdirectories.add(path)
            else:
                try:
                    file = File.match(path)
                except FileError as error:
                    self.errors.append(str(error))
                    continue
                self.files.add(file)

    def parse(self):
        if self.is_parsed:
            return
        for file in self.files:
            file.parse()
        self.is_parsed = True


class Chapter(DeterministicDatabaseRecord):
    DETERMINANT_FIELDS = ["file_id", "title"]

    title: str
    tags: t.Sequence[Tag] = Field(default=[])

    file_id: ID


class Note(DeterministicDatabaseRecord):
    DETERMINANT_FIELDS = ["file_id", "title"]

    title: str
    text: str
    tags: t.Sequence[Tag] = Field(default=[])
    pages: t.Sequence[str] = Field(default=[])

    file_id: ID
    chapter_id: t.Optional[ID] = None


Question = Note


class Paragraph(DeterministicDatabaseRecord):
    DETERMINANT_FIELDS = ["file_id", "title"]

    title: str
    text: str
    file_id: ID


class Quote(DeterministicDatabaseRecord):
    DETERMINANT_FIELDS = ["file_id", "text"]

    text: str
    author: str
    page: str

    note_id: ID
    file_id: ID


class Thought(DeterministicDatabaseRecord):
    DETERMINANT_FIELDS = ["file_id", "text"]

    text: str
    tags: t.Sequence[Tag] = Field(default=[])
    date_: datetime = Field(alias="date")
    file_id: ID

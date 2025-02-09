import os
import typing as t
from datetime import datetime
from pathlib import Path

from indigo.database.models import (
    DeterministicDatabaseRecord,
    Field,
)
from indigo.models.base import ID
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

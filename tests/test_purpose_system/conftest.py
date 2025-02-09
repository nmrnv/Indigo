import typing as t
from datetime import datetime
from pathlib import Path

from indigo.models.patterns import SEPARATOR
from indigo.systems.purpose.files import (
    DiaryFile,
    EssayFile,
    NoteFile,
    RootFile,
    StudyFile,
    ThoughtsFile,
    WordsFile,
)
from indigo.utils import date_utils
from tests.conftest import FileMock


def make_mock_root_file(
    path: Path, name: t.Optional[str] = None
) -> RootFile:
    root_file_path = (
        path / f"_{path.name}.md" if not name else path / f"_{name}.md"
    )
    name = (name or path.name).capitalize().replace("_", " ")
    file = FileMock(root_file_path)
    file.write(
        f"## {name.capitalize().replace('_', '')}",
        f"`[{RootFile.FILE_TAG}]`",
        SEPARATOR,
        "# Synopsis",
        "Mock note synopsis",
        SEPARATOR,
        "# Note",
        "Mock note text",
    )
    return RootFile.match(root_file_path)


def make_mock_note_file(path: Path, name: str) -> NoteFile:
    name = f"{name}.md"
    file = FileMock(path / name)
    file.write(
        f"## {name.capitalize().replace('_', '')}",
        f"`[{NoteFile.FILE_TAG}]`",
        SEPARATOR,
        "# Synopsis",
        "Mock note synopsis",
        SEPARATOR,
        "# Note",
        "Mock note text",
    )
    return NoteFile.match(file.path)


def make_mock_essay_file(path: Path, title: str) -> EssayFile:
    name = f"{title.lower().replace(' ', '_')}.md"
    file = FileMock(path / name)
    file.write(
        f"## {title}",
        f"`[{EssayFile.FILE_TAG}]`",
        SEPARATOR,
        "# Purpose and key points",
        "For testing",
        SEPARATOR,
        "# Outline",
        "- Paragraph one",
        SEPARATOR,
        SEPARATOR,
        "## Draft",
        SEPARATOR,
        "# Paragraph one",
        "Paragraph one text",
    )
    return EssayFile.match(file.path)


def make_mock_thoughts_file(path: Path, date: datetime) -> ThoughtsFile:
    date = date_utils.beginning_of_month(date)
    year, month = (
        date.year,
        date.month if len(str(date.month)) == 2 else f"0{date.month}",
    )
    name = f"{year}.{month}_Thoughts.md"
    file = FileMock(path / name)
    file.write(
        f"## {year}.{month} Thoughts",
        f"`[{ThoughtsFile.FILE_TAG}]`",
        SEPARATOR,
        "This is a mock thought for testing",
        "`[testing]`",
    )
    return ThoughtsFile.match(file.path)


def make_mock_diary_file(path: Path, date: datetime) -> DiaryFile:
    date = date_utils.beginning_of_month(date)
    year, month = (
        date.year,
        date.month if len(str(date.month)) == 2 else f"0{date.month}",
    )
    name = f"{year}.{month}_Diary.md"
    file = FileMock(path / name)
    file.write(
        f"## {year}.{month} Diary",
        f"`[{DiaryFile.FILE_TAG}]`",
        SEPARATOR,
        "# 21st of January, Friday",
        "This is a mock diary entry",
    )
    return DiaryFile.match(file.path)


def make_mock_study_file(path: Path, name: str) -> StudyFile:
    name = f"{name}.md"
    file = FileMock(path / name)
    file.write(
        f"## {name.capitalize().replace('_', '')}",
        f"`[{StudyFile.FILE_TAG}]`",
        SEPARATOR,
        "# Synopsis",
        "Mock synopsis",
        SEPARATOR,
        SEPARATOR,
        "## Primary Ideas",
        SEPARATOR,
        "# Note",
        "`[note_tag]`",
        "Note text",
    )
    return StudyFile.match(file.path)


def make_mock_words_file(path: Path, date: datetime) -> WordsFile:
    date = date_utils.beginning_of_month(date)
    year, month = (
        date.year,
        date.month if len(str(date.month)) == 2 else f"0{date.month}",
    )
    name = f"{year}.{month}_Words.md"
    file = FileMock(path / name)
    file.write(
        f"## {year}.{month} Words",
        f"`[{WordsFile.FILE_TAG}][english]`",
        SEPARATOR,
        "# Mock",
        "`[noun][1]`",
        "1. A dummy object",
        "  - Tests use mock objects",
    )
    return WordsFile.match(file.path)

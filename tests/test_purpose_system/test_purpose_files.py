from datetime import datetime
from pathlib import Path

import pytest
from freezegun import freeze_time
from librum.files import FileError
from librum.patterns import SEPARATOR

from indigo.systems.purpose.files import (
    DiaryFile,
    EssayFile,
    NoteFile,
    RootFile,
    StudyFile,
    ThoughtsFile,
)
from indigo.utils import date_utils
from tests.conftest import FileMock


def test_note_file(test_file: FileMock):
    # Given
    test_file.write(
        "## Note",
        "`[note_file][philosophy]`",
        SEPARATOR,
        "# Synopsis",
        "Note synopsis",
        SEPARATOR,
        "# Some note",
        "Some note text",
        SEPARATOR,
        "# Another note",
        "`[ethics]`",
        "Another note text",
    )

    # When
    file = NoteFile(test_file.path)
    file.parse()

    # Then
    assert file.title == "Note"
    assert file.tags == ["philosophy"]

    assert len(file.notes) == 2
    note = file.notes[0]
    assert note.title == "Some note"
    assert note.tags == ["philosophy"]
    assert note.text == "Some note text"
    assert note.file_id == file.record.id_

    note = file.notes[1]
    assert note.title == "Another note"
    assert note.tags == ["philosophy", "ethics"]
    assert note.text == "Another note text"
    assert note.file_id == file.record.id_

    record = file.record
    assert record.file_tag == "note_file"
    assert record.path == test_file.path
    assert record.title == "Note"
    assert record.tags == ["philosophy"]
    assert isinstance(record.created_at, datetime)
    assert isinstance(record.updated_at, datetime)


def test_note_file_minimal(test_file: FileMock):
    # Given
    test_file.write(
        "## Note",
        "`[note_file]`",
        SEPARATOR,
        "# Some note",
        "Some note text",
    )

    # When
    file = NoteFile(test_file.path)
    file.parse()

    # Then
    assert len(file.notes) == 1
    assert not file.notes[0].tags


def test_root_file(test_file: FileMock):
    # Given
    test_file.write(
        "## Test file",
        "`[root_file][philosophy]`",
        SEPARATOR,
        "# Synopsis",
        "Root file synopsis",
        SEPARATOR,
        "# Some note",
        "Some note text",
    )

    # When
    file = RootFile(test_file.path)
    file.parse()

    # Then
    assert file.title == "Test file"
    assert file.tags == ["philosophy"]

    record = file.record
    assert record.file_tag == "root_file"
    assert record.path == test_file.path
    assert record.title == "Test file"
    assert record.tags == ["philosophy"]
    assert isinstance(record.created_at, datetime)
    assert isinstance(record.updated_at, datetime)


def test_root_file_with_invalid_name(test_file: FileMock):
    # Given
    test_file.write(
        "## Invalid name",
        "`[root_file]`",
        SEPARATOR,
        "# Synopsis",
        "Root file synopsis",
        SEPARATOR,
        "# Some note",
        "Some note text",
    )
    file = RootFile(test_file.path)

    # Then
    with pytest.raises(FileError):
        # When
        file.parse()


@freeze_time("01/01/2022")
def test_diary_file(tmp_path: Path):
    # Given
    file = FileMock(tmp_path / "2022.01_Diary.md")
    file.write(
        "## 2022.01 Diary",
        "`[diary_file]`",
        SEPARATOR,
        "# 3rd of January, Monday",
        "Entry text",
        SEPARATOR,
        "# 21st of January, Friday",
        "Entry text",
    )

    # When
    file = DiaryFile(file.path)
    file.parse()

    # Then
    assert file.date_ == date_utils.beginning_of_day()

    record = file.record
    assert record.file_tag == "diary_file"
    assert record.path == file.path
    assert record.title == "2022.01 Diary"
    assert record.tags == []
    assert isinstance(record.created_at, datetime)
    assert isinstance(record.updated_at, datetime)


@freeze_time("01/01/2022")
def test_diary_file_invalid_filename(tmp_path: Path):
    # Given
    file = FileMock(tmp_path / "2022.01_Diary.md")
    file.write(
        "## 2022.02 Diary",
        "`[diary_file]`",
        SEPARATOR,
        "# 3rd of January, Monday",
        "Entry text",
    )
    file = DiaryFile(file.path)

    # Then
    with pytest.raises(
        FileError,
        match=(
            "DatedRecordedFile: Filename '2022.01_Diary.md' "
            "does not match the header-derived '2022.02_Diary.md'."
        ),
    ):
        file.parse()


@freeze_time("01/01/2022")
def test_diary_file_invalid_entry_month(tmp_path: Path):
    # Given
    file = FileMock(tmp_path / "2022.01_Diary.md")
    file.write(
        "## 2022.01 Diary",
        "`[diary_file]`",
        SEPARATOR,
        "# 3rd of February, Monday",
        "Entry text",
    )
    file = DiaryFile(file.path)

    # Then
    with pytest.raises(
        FileError,
        match=(
            "DiaryFile: Entry month February does not match file month"
            " January."
        ),
    ):
        file.parse()


@freeze_time("01/01/2022")
def test_diary_file_invalid_entry_order(tmp_path: Path):
    # Given
    file = FileMock(tmp_path / "2022.01_Diary.md")
    file.write(
        "## 2022.01 Diary",
        "`[diary_file]`",
        SEPARATOR,
        "# 3rd of January, Monday",
        "Entry text",
        SEPARATOR,
        "# 1st of January, Saturday",
        "Entry text",
    )
    file = DiaryFile(file.path)

    # Then
    with pytest.raises(
        FileError,
        match=(
            "DiaryFile: Entry on date 01/01/2022 should not "
            "be listed before the one on 03/01/2022."
        ),
    ):
        file.parse()


@freeze_time("01/01/2022")
def test_diary_file_invalid_entry_weekday(tmp_path: Path):
    # Given
    file = FileMock(tmp_path / "2022.01_Diary.md")
    file.write(
        "## 2022.01 Diary",
        "`[diary_file]`",
        SEPARATOR,
        "# 3rd of January, Sunday",
        "Entry text",
    )
    file = DiaryFile(file.path)

    # Then
    with pytest.raises(
        FileError,
        match=(
            "DiaryFile: Invalid weekday Sunday for entry"
            " on 03/01/2022. Should be Monday."
        ),
    ):
        file.parse()


@freeze_time("01/01/2022")
def test_thoughts_file(tmp_path: Path):
    # Given
    file = FileMock(tmp_path / "2022.01_Thoughts.md")
    file.write(
        "## 2022.01 Thoughts",
        "`[thoughts_file]`",
        SEPARATOR,
        "Political thought",
        "`[politics]`",
        SEPARATOR,
        "Philosophical thought",
        "`[philosophy]`",
    )

    # When
    file = ThoughtsFile(file.path)
    file.parse()

    # Then
    assert file.date_ == date_utils.beginning_of_day()
    assert len(file.thoughts) == 2

    thought = file.thoughts[0]
    assert thought.text == "Political thought"
    assert thought.tags == ["politics"]
    assert thought.date_ == date_utils.beginning_of_day()

    second_thought = file.thoughts[1]
    assert second_thought.text == "Philosophical thought"
    assert second_thought.tags == ["philosophy"]
    assert second_thought.date_ == date_utils.beginning_of_day()

    record = file.record
    assert record.file_tag == "thoughts_file"
    assert record.path == file.path
    assert not record.tags
    assert isinstance(record.created_at, datetime)
    assert isinstance(record.updated_at, datetime)


@freeze_time("01/01/2022")
def test_thoughts_file_invalid_filename(tmp_path: Path):
    # Given
    file = FileMock(tmp_path / "2022.01_Thoughts.md")
    file.write(
        "## 2022.02 Thoughts",
        "`[thoughts_file]`",
        SEPARATOR,
        "# Thought",
        "`[poetics]`",
        "Thought text",
    )
    file = ThoughtsFile(file.path)

    # Then
    with pytest.raises(
        FileError,
        match=(
            "DatedRecordedFile: Filename '2022.01_Thoughts.md' "
            "does not match the header-derived '2022.02_Thoughts.md'."
        ),
    ):
        file.parse()


@freeze_time("01/01/2022")
def test_thoughts_file_with_duplicate_thoughts(tmp_path: Path):
    # Given
    file = FileMock(tmp_path / "2022.01_Thoughts.md")
    file.write(
        "## 2022.01 Thoughts",
        "`[thoughts_file]`",
        SEPARATOR,
        "Political thought",
        "`[politics]`",
        SEPARATOR,
        "Political thought",
        "`[politics]`",
    )
    file = ThoughtsFile(file.path)

    # Then
    with pytest.raises(
        FileError,
        match="ThoughtsFile: Cannot have duplicate thoughts.",
    ):
        # When
        file.parse()


def test_essay_file_create(tmp_path: Path):
    # Given
    path = tmp_path / "essay.md"

    # When
    EssayFile.create(path, "Essay")
    file = EssayFile(path)
    file.parse()

    # Then
    assert file.title == "Essay"
    assert file.tags == []
    assert file.path == path


def test_essay_file(tmp_path: Path):
    # Given
    test_file = FileMock(tmp_path / "Essay_I.md")
    test_file.write(
        "## Essay",
        "`[essay_file][philosophy]`",
        SEPARATOR,
        "# Purpose and key points",
        "The purpose of this essay",
        "in two lines",
        SEPARATOR,
        "# Note",
        "Note text",
        SEPARATOR,
        "# Another note",
        "Another note text",
        SEPARATOR,
        SEPARATOR,
        "## Draft",
        "Draft text",
        SEPARATOR,
        "# Paragraph one",
        "Paragraph text",
        SEPARATOR,
        "On multi line",
        SEPARATOR,
        "# Paragraph two",
        "Paragraph two text",
        SEPARATOR,
        "# References",
        "1. Referenced source",
    )

    # When
    file = EssayFile(test_file.path)
    file.parse()

    # Then
    assert file.title == "Essay"
    assert file.tags == ["philosophy"]
    assert file.purpose == "The purpose of this essay\nin two lines"

    assert len(file.notes) == 2
    assert file.notes[0].title == "Note"
    assert file.notes[0].text == "Note text"
    assert file.notes[1].title == "Another note"
    assert file.notes[1].text == "Another note text"

    assert len(file.paragraphs) == 2
    assert file.paragraphs[0].title == "Paragraph one"
    assert file.paragraphs[0].text == "Paragraph text\n\nOn multi line"
    assert file.paragraphs[1].title == "Paragraph two"
    assert file.paragraphs[1].text == "Paragraph two text"
    assert file.references == ["Referenced source"]

    record = file.record
    assert record.file_tag == "essay_file"
    assert record.path == test_file.path
    assert record.title == "Essay"
    assert record.tags == ["philosophy"]
    assert isinstance(record.created_at, datetime)
    assert isinstance(record.updated_at, datetime)


def test_study_file(test_file: FileMock):
    # Given
    test_file.write(
        "## Study file",
        "`[study_file][root_tag]`",
        SEPARATOR,
        "# Synopsis",
        "Synopsis text",
        SEPARATOR,
        "# Side note",
        "Note without tags",
        SEPARATOR,
        SEPARATOR,
        "## Primary Ideas",
        SEPARATOR,
        "# Primary note",
        "`[primary_note_tag]`",
        "Primary note text",
        SEPARATOR,
        "# Primary question?",
        "`[primary_question_tag]`",
        "Primary question text",
        SEPARATOR,
        "E) Excerpt text",
        SEPARATOR,
        'Q) "Quote text", Arthur Schopenhauer, page 123',
        SEPARATOR,
        "Some extra text",
        SEPARATOR,
        SEPARATOR,
        "## Secondary Ideas",
        SEPARATOR,
        "# Secondary question?",
        "`[secondary_question_tag]`",
        "Secondary question text",
        SEPARATOR,
        SEPARATOR,
        "## Remarks",
        SEPARATOR,
        "# Remark",
        "`[purpose]`",
        "Remark text",
    )

    # When
    file = StudyFile(test_file.path)
    file.parse()

    # Then
    assert file.title == "Study file"
    assert file.tags == ["root_tag"]

    assert len(file.notes) == 5

    note_one = file.notes[0]
    assert note_one.title == "Side note"
    assert note_one.text == "Note without tags"
    assert note_one.tags == ["root_tag"]
    assert note_one.file_id == file.record.id_

    note_two = file.notes[1]
    assert note_two.title == "Primary note"
    assert note_two.text == "Primary note text"
    assert note_two.tags == ["root_tag", "primary_note_tag"]
    assert note_two.file_id == file.record.id_

    note_three = file.notes[2]
    assert note_three.title == "Primary question?"
    assert (
        note_three.text == "Primary question text\n\n"
        "Excerpt: Excerpt text\n\n"
        "Some extra text"
    )
    assert note_three.tags == ["root_tag", "primary_question_tag"]
    assert note_three.file_id == file.record.id_

    note_four = file.notes[3]
    assert note_four.title == "Secondary question?"
    assert note_four.text == "Secondary question text"
    assert note_four.tags == ["root_tag", "secondary_question_tag"]
    assert note_four.file_id == file.record.id_

    assert len(file.quotes) == 1
    quote_one = file.quotes[0]
    assert quote_one.text == "Quote text"
    assert quote_one.author == "Arthur Schopenhauer"
    assert quote_one.page == "123"
    assert quote_one.note_id == file.notes[2].id_
    assert quote_one.file_id == file.record.id_

    record = file.record
    assert record.file_tag == "study_file"
    assert record.path == test_file.path
    assert record.title == "Study file"
    assert record.tags == ["root_tag"]
    assert isinstance(record.created_at, datetime)
    assert isinstance(record.updated_at, datetime)


def test_study_file_without_optional_sections(test_file: FileMock):
    # Given
    test_file.write(
        "## Study file",
        "`[study_file]`",
        SEPARATOR,
        "# Synopsis",
        "Synopsis text",
        SEPARATOR,
        SEPARATOR,
        "## Primary Ideas",
        SEPARATOR,
        "# Note one",
        "`[note_tag]`",
        "Note one text",
    )

    # When
    file = StudyFile(test_file.path)
    file.parse()

    # Then
    assert len(file.notes) == 1


@pytest.mark.parametrize("header", ["Note", "Question?"])
def test_study_file_failure_note_or_question_duplicates_file_tags(
    test_file: FileMock, header: str
):
    # Given
    test_file.write(
        "## Study file",
        "`[study_file][duplicate]`",
        SEPARATOR,
        "# Synopsis",
        "Synopsis text",
        SEPARATOR,
        f"# {header}",
        "`[duplicate]`",
        "Note text",
    )

    file = StudyFile(test_file.path)

    # Then
    with pytest.raises(
        FileError,
        match="StudyFile: Notes and questions cannot duplicate file tags.",
    ):
        # When
        file.parse()

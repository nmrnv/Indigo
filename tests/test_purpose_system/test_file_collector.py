from pathlib import Path

import pytest

from indigo.config import Config
from indigo.systems.purpose.file_collector import FileCollector
from indigo.utils import date_utils
from tests.test_purpose_system.conftest import (
    make_mock_essay_file,
    make_mock_note_file,
    make_mock_root_file,
    make_mock_study_file,
    make_mock_thoughts_file,
)


@pytest.fixture
def notes_directory(frozen_time) -> Path:
    """Valid, populated notes directory"""
    frozen_time.move_to("01/01/2022")
    router = Config.router
    today = date_utils.today()

    # Fill notes directory
    make_mock_root_file(router.notes_directory)

    # Fill purpose directory
    (router.notes_directory / "purpose").mkdir()
    make_mock_root_file(router.purpose_directory)
    make_mock_note_file(router.purpose_directory, "test_note")

    # Fill thoughts directory
    (router.notes_directory / "thoughts").mkdir()
    make_mock_thoughts_file(router.thoughts_directory, date=today)

    # Fill studies directory
    (router.notes_directory / "studies").mkdir()
    make_mock_root_file(router.studies_directory)
    (router.studies_directory / "philosophy").mkdir()
    make_mock_root_file(router.studies_directory / "philosophy")
    make_mock_study_file(
        router.studies_directory / "philosophy", "the_republic"
    )

    # Fill personal directory
    make_mock_root_file(router.notes_directory / "personal")

    # Fill archive directory
    make_mock_note_file(router.archive_directory, "archived_test_note")

    # Make essays directory
    make_mock_root_file(router.essays_directory)
    make_mock_essay_file(router.essays_directory, "Essay")

    # Make languages directory
    languages_directory = router.studies_directory / "languages"
    make_mock_root_file(languages_directory)
    make_mock_root_file(languages_directory / "english")

    return router.notes_directory


@pytest.fixture
def collector() -> FileCollector:
    return FileCollector()


def test_file_collector_relative_path(collector: FileCollector):
    # When
    philosophy_directory = (
        collector.router.notes_directory / "directory" / "note.md"
    )

    # Then
    assert collector.relative_to_root(philosophy_directory) == Path(
        "directory/note.md"
    )


def test_collect_files_full(
    collector: FileCollector, notes_directory: Path
):
    # When
    result = collector.collect_files(notes_directory)

    # Then
    assert not result.errors
    assert len(result.records) == 15


def test_collect_files_failure_non_md_file(
    collector: FileCollector, notes_directory: Path
):
    # Given
    (notes_directory / "not_an_md_file").touch()

    # When
    result = collector.collect_files(notes_directory)

    # Then
    assert not result.records
    assert result.errors == ["File 'not_an_md_file' is not a .md file."]


def test_collect_files_failure_empty_directory(
    collector: FileCollector, notes_directory: Path
):
    # Given
    (notes_directory / "empty_directory").mkdir()

    # When
    result = collector.collect_files(notes_directory)

    # Then
    assert not result.records
    assert result.errors == [
        "Directory 'empty_directory' does not contain any files."
    ]


def test_collect_files_failure_missing_root_file(
    collector: FileCollector, notes_directory: Path
):
    # Given
    test_directory = notes_directory / "test_directory"
    test_directory.mkdir()
    make_mock_note_file(test_directory, "test_note.md")

    # When
    result = collector.collect_files(notes_directory)

    # Then
    assert not result.records
    assert result.errors == ["There is no root file at 'test_directory'."]


def test_collect_files_failure_more_than_one_root_file(
    collector: FileCollector, notes_directory: Path
):
    # Given
    make_mock_root_file(notes_directory, "extra_root")

    # When
    result = collector.collect_files(notes_directory)

    # Then
    assert not result.records
    assert result.errors == [
        "Directory '.' contains more than one root file."
    ]


@pytest.mark.parametrize("difference", (1, -1))
def test_collect_files_failure_yearly_directory_files_not_from_this_year(
    collector: FileCollector, notes_directory: Path, difference: int
):
    # Given
    words_directory = collector.router.words_directory
    today = date_utils.today()
    differing_date = today.replace(year=today.year + difference)
    make_mock_words_file(words_directory, date=differing_date)

    # When
    result = collector.collect_files(notes_directory)

    # Then
    assert not result.records
    assert result.errors == [
        "The names of all files in 'words' must begin with the current"
        " year."
    ]


def test_collect_files_failure_two_level_subdirectory_in_yearly_directory(
    collector: FileCollector, notes_directory: Path
):
    # Given
    words_directory = collector.router.words_directory
    today = date_utils.today()
    last_year = today.replace(year=today.year - 1)
    last_year_directory = words_directory / str(last_year.year)
    last_year_directory.mkdir()
    make_mock_words_file(last_year_directory, date=last_year)

    (last_year_directory / "invalid_directory").mkdir()

    # When
    result = collector.collect_files(notes_directory)

    # Then
    assert not result.records
    assert result.errors == [
        "'studies/languages/english/words' must not have two levels of"
        " sub-directories."
    ]


def test_collect_files_failure_yearly_subdirectory_not_named_after_a_year(
    collector: FileCollector, notes_directory: Path
):
    # Given
    words_directory = collector.router.words_directory
    (words_directory / "invalid_directory").mkdir()

    # When
    result = collector.collect_files(notes_directory)

    # Then
    assert not result.records
    assert result.errors == [
        "Yearly subdirectory 'invalid_directory' in 'words' must be named"
        " after a year."
    ]


def test_collect_files_failure_yearly_subdirectory_files_not_from_matching_year(
    collector: FileCollector, notes_directory: Path
):
    # Given
    words_directory = collector.router.words_directory
    today = date_utils.today()
    last_year = today.replace(year=today.year - 1)
    last_year_directory = words_directory / str(last_year.year)
    last_year_directory.mkdir()

    make_mock_words_file(last_year_directory, date=today)

    # When
    result = collector.collect_files(notes_directory)

    # Then
    assert not result.records
    assert result.errors == [
        "All files in 'studies/languages/english/words/2021' "
        "must be from the year '2021'."
    ]


def test_collect_files_failure_contains_not_allowed_files(
    collector: FileCollector, notes_directory: Path
):
    # Given
    today = date_utils.today()
    make_mock_thoughts_file(collector.router.essays_directory, date=today)

    # When
    result = collector.collect_files(notes_directory)

    # Then
    assert not result.records
    assert result.errors == [
        (
            "Thoughts files must not exist outside the thoughts"
            " directory.\nError in 'purpose/essays'."
        ),
        "Essays directory contains other than essay & root files.",
    ]


def test_collect_files_failure_child_contains_not_allowed_files(
    collector: FileCollector, notes_directory: Path
):
    # Given
    pytest.fail()
    diary_directory = collector.router.diary_directory
    today = date_utils.today()
    last_year = today.replace(year=today.year - 1)
    last_year_directory = diary_directory / str(last_year.year)
    last_year_directory.mkdir()

    make_mock_note_file(last_year_directory, "unaccepted")
    (last_year_directory / "unaccepted.md").rename(
        last_year_directory / "2021_Note.md"
    )

    # When
    result = collector.collect_files(notes_directory)

    # Then
    assert not result.records
    assert result.errors == [
        "'Diary/2021' directory contains other than diary files."
    ]


def test_collect_files_failure_other_directory_contains_allowed_files(
    collector: FileCollector, notes_directory: Path
):
    # Given
    make_mock_essay_file(collector.router.notes_directory, title="Essay")

    # When
    result = collector.collect_files(notes_directory)

    # Then
    assert not result.records
    assert result.errors == [
        "Essay files must not exist outside the essays directory.\nError in"
        " 'notes'."
    ]


def test_collect_files_failure_root_not_allowed_in_validated_directory(
    collector: FileCollector, notes_directory: Path
):
    # Given
    test_directory = notes_directory / "test"
    test_directory.mkdir()

    # Custom setup, because this test is impossible otherwise
    collector.validators = [
        *collector.validators,
        collector._make_validator(
            expected_directory=test_directory, expected_file_tag="some_file"
        ),
    ]
    make_mock_root_file(test_directory)

    # When
    result = collector.collect_files(notes_directory)

    # Then
    assert not result.records
    assert result.errors == [
        "Test directory contains other than some files."
    ]

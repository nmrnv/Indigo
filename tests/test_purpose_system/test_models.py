from pathlib import Path

import pytest
from librum.files import File

from indigo.systems.purpose.models import Directory, DirectoryError


def test_directory_init(tmp_path: Path):
    # Given
    directory_path = tmp_path / "directory"
    directory_path.mkdir()

    (directory_path / "file_one").write_text("# File\n`[note_file]`\n")
    (directory_path / "file_two").write_text("# File\n`[study_file]`\n")
    (directory_path / "directory_one").mkdir()
    (directory_path / "directory_two").mkdir()

    # When
    directory = Directory(location=directory_path)

    # Then
    assert directory.location == directory_path
    assert directory.files == {
        File.match(directory_path / "file_one"),
        File.match(directory_path / "file_two"),
    }
    assert directory.subdirectories == {
        directory_path / "directory_one",
        directory_path / "directory_two",
    }

    assert not directory.is_parsed
    assert not directory.file_records
    assert not directory.errors


def test_directory_init_fails_on_file(tmp_path: Path):
    # Given
    filepath = tmp_path / "file"
    filepath.touch()

    # Then
    with pytest.raises(
        DirectoryError,
        match="Cannot initialise Directory",
    ):
        # When
        Directory(location=filepath)

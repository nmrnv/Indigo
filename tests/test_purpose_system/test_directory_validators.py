from pathlib import Path


def test_no_files_validator(tmp_path: Path):
    # Given
    directory = tmp_path / "directory"
    directory.mkdir()

    # When

import subprocess
import sys
import typing as t
from pathlib import Path

sys.path.append(Path().parent.as_posix())

from indigo.models.base import Model
from indigo.utils import date_utils
from indigo.utils.path_utils import (
    get_directory_size,
    get_directory_structure,
)


class ArchiveMetadata(Model):
    mongodb_size: int
    mongodb_structure: t.Mapping
    mongodb_readable_size: int
    mongodb_readable_structure: t.Mapping
    notes_directory_size: int
    notes_directory_structure: t.Mapping
    commit_hash: str
    datetime_str: str

    @classmethod
    def generate(cls, archive_directory: Path) -> "ArchiveMetadata":
        mongodb_directory = archive_directory / "mongodb"
        mongodb_size = get_directory_size(mongodb_directory)
        mongodb_structure = get_directory_structure(mongodb_directory)

        mongodb_readable_size_directory = (
            archive_directory / "mongodb_readable"
        )
        mongo_db_readable_size = get_directory_size(
            mongodb_readable_size_directory
        )
        mongo_db_readable_structure = get_directory_structure(
            mongodb_readable_size_directory
        )

        notes_directory = archive_directory / "notes"
        notes_directory_size = get_directory_size(notes_directory)
        notes_directory_structure = get_directory_structure(notes_directory)

        git_rev_parse = subprocess.run(
            "git rev-parse HEAD", shell=True, capture_output=True
        )
        current_commit_hash = git_rev_parse.stdout.decode(
            encoding="utf-8"
        ).strip()

        return cls(
            mongodb_size=mongodb_size,
            mongodb_structure=mongodb_structure,
            mongodb_readable_size=mongo_db_readable_size,
            mongodb_readable_structure=mongo_db_readable_structure,
            notes_directory_size=notes_directory_size,
            notes_directory_structure=notes_directory_structure,
            commit_hash=current_commit_hash,
            datetime_str=date_utils.datetime_str(date_utils.now()),
        )

import re
import typing as t
from dataclasses import dataclass
from pathlib import Path

from indigo.systems.purpose.files import RootFile
from indigo.systems.purpose.models import FileRecord
from indigo.utils import date_utils

FILE_TAG = str


@dataclass
class Directory:
    path: Path
    subdirectories: t.Sequence[Path]
    filepaths: t.Sequence[Path]
    file_records: t.List[FileRecord]
    file_tags: t.List[FILE_TAG]
    errors: t.List[str]


def no_files_validator(directory: Directory):
    if not directory.filepaths:
        directory.errors.append(
            f"Directory {directory.path.name!r} does not contain any files."
        )


def non_markdown_files_validator(directory: Directory):
    for file in directory.filepaths:
        if not file.name.endswith(".md"):
            directory.errors.append(
                f"Directory {directory.path.name!r} contains non-markdown"
                " files."
            )


def no_subdirectories_validator(directory: Directory):
    if directory.subdirectories:
        directory.errors.append(
            f"Directory {directory.path.name!r} must not contain"
            " subdirectories."
        )


def root_file_validator(directory: Directory):
    root_file_count = 0
    for tag in directory.file_tags:
        if tag == RootFile.FILE_TAG:
            root_file_count += 1
    if root_file_count != 1:
        directory.errors.append(
            f"Directory {directory.path.name!r} must contain only one root"
            " file."
        )


def no_root_file_validator(directory: Directory):
    if RootFile.FILE_TAG in directory.file_tags:
        directory.errors.append(
            f"Directory {directory.path.name!r} must not contain a root"
            " file."
        )


def only_root_file_validator(directory: Directory):
    if directory.file_tags != [RootFile.FILE_TAG]:
        directory.errors.append(
            f"Directory {directory.path.name!r} must only contain a root"
            " file."
        )


def notes_directory_validator(directory: Directory):
    for tag in directory.file_tags:
        if tag not in (RootFile.FILE_TAG, NoteFile.FILE_TAG):
            directory.errors.append(
                f"Directory {directory.path.name!r} should only contain"
                f" a root file and note files, not {tag!r} files."
            )


def allowed_file_tags_validator(
    directory: Directory, allowed_tags: t.Set[FILE_TAG]
):
    if set(directory.file_tags) != allowed_tags:
        directory.errors.append(
            f"Directory {directory.path.name!r} should only"
            f" contain {allowed_tags!r} files."
        )


def yarly_directory_current_year_validator(directory: Directory):
    for file in directory.filepaths:
        if not file.name.startswith(str(date_utils.now().year)):
            directory.errors.append(
                f"Directory {directory.path.name!r}'s files"
                " must be prefixed with the current year."
            )


def yearly_directory_subdirectories_validator(directory: Directory):
    for subdirectory in directory.subdirectories:
        if not re.match(r"^[2-9][0-9]{3}$", subdirectory.name):
            directory.errors.append(
                f"Directory {directory.path.name!r}'s"
                " subdirectories must be prefixed with a year."
            )


def yearly_directory_parent_year_validator(directory: Directory):
    parent_year = directory.path.parent.name
    for file in directory.filepaths:
        if not file.name.startswith(parent_year):
            directory.errors.append(
                f"Directory {directory.path.name!r}'s files"
                f" must be from the year {parent_year!r}."
            )


def archive_validator(directory: Directory):
    for file in directory.filepaths:
        if not file.name.startswith("archived_"):
            directory.errors.append(
                f"Directory {directory.path.name!r} files"
                " should be prefixed with `_archived`."
            )

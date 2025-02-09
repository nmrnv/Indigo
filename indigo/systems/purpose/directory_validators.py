import functools
import re
import typing as t
from copy import copy

from indigo.base import Error
from indigo.systems.purpose.files import (
    EssayFile,
    NoteFile,
    RootFile,
    StudyFile,
    ThoughtsFile,
)
from indigo.systems.purpose.models import Directory, Tag
from indigo.utils import date_utils


class DirectoryValidationError(Error): ...


def no_files_validator(directory: Directory):
    if not directory.filepaths:
        directory.errors.append(
            f"Directory {directory.location.name!r} does not contain any files."
        )


def non_markdown_files_validator(directory: Directory):
    for file in directory.files:
        if not file.path.name.endswith(".md"):
            directory.errors.append(
                f"Directory {directory.location.name!r} contains non-markdown"
                " files."
            )


def no_subdirectories_validator(directory: Directory):
    if directory.subdirectories:
        directory.errors.append(
            f"Directory {directory.location.name!r} must not contain"
            " subdirectories."
        )


def root_file_validator(directory: Directory):
    root_file_count = 0
    for tag in directory.file_tags:
        if tag == RootFile.FILE_TAG:
            root_file_count += 1
    if root_file_count != 1:
        directory.errors.append(
            f"Directory {directory.location.name!r} must contain only one root"
            " file."
        )


def no_root_file_validator(directory: Directory):
    if RootFile.FILE_TAG in directory.file_tags:
        directory.errors.append(
            f"Directory {directory.location.name!r} must not contain a root"
            " file."
        )


def only_root_file_validator(directory: Directory):
    if directory.file_tags != [RootFile.FILE_TAG]:
        directory.errors.append(
            f"Directory {directory.location.name!r} must only contain a root"
            " file."
        )


def notes_directory_validator(directory: Directory):
    for tag in directory.file_tags:
        if tag not in (RootFile.FILE_TAG, NoteFile.FILE_TAG):
            directory.errors.append(
                f"Directory {directory.location.name!r} should only contain"
                f" a root file and note files, not {tag!r} files."
            )


def allowed_file_tags_validator(
    directory: Directory, allowed_tags: t.Set[Tag]
):
    if set(directory.file_tags) != allowed_tags:
        directory.errors.append(
            f"Directory {directory.location.name!r} should only"
            f" contain {allowed_tags!r} files."
        )


def yarly_directory_current_year_validator(directory: Directory):
    for file in directory.filepaths:
        if not file.name.startswith(str(date_utils.now().year)):
            directory.errors.append(
                f"Directory {directory.location.name!r}'s files"
                " must be prefixed with the current year."
            )


def yearly_directory_subdirectories_validator(directory: Directory):
    for subdirectory in directory.subdirectories:
        if not re.match(r"^[2-9][0-9]{3}$", subdirectory.name):
            directory.errors.append(
                f"Directory {directory.location.name!r}'s"
                " subdirectories must be prefixed with a year."
            )


def yearly_directory_parent_year_validator(directory: Directory):
    parent_year = directory.location.parent.name
    for file in directory.filepaths:
        if not file.name.startswith(parent_year):
            directory.errors.append(
                f"Directory {directory.location.name!r}'s files"
                f" must be from the year {parent_year!r}."
            )


def archive_validator(directory: Directory):
    for file in directory.filepaths:
        if not file.name.startswith("archived_"):
            directory.errors.append(
                f"Directory {directory.location.name!r} files"
                " should be prefixed with `_archived`."
            )


class DirectoryValidators:
    validators: t.Sequence[t.Callable]
    subdirectory_validators: t.Sequence[t.Callable]

    def __init__(
        self,
        validators: t.Sequence[t.Callable],
        subdirectory_validators: t.Sequence[t.Callable] = [],
        apply_validators_to_subdirectories: bool = False,
    ):
        self.validators = [
            *validators,
            no_files_validator,
            non_markdown_files_validator,
        ]
        self.subdirectory_validators = [
            *subdirectory_validators,
            no_files_validator,
            non_markdown_files_validator,
        ]
        if apply_validators_to_subdirectories:
            subdirectory_validators_ = list(copy(subdirectory_validators))
            for validator in validators:
                if validator not in subdirectory_validators:
                    subdirectory_validators_.append(validator)
            self.subdirectory_validators = subdirectory_validators_


DIRECTORY_VALIDATORS = {
    # Purpose
    "purpose": DirectoryValidators(
        validators=[root_file_validator],
        subdirectory_validators=[],
    ),
    "purpose/essays": DirectoryValidators(
        validators=[
            no_root_file_validator,
            no_subdirectories_validator,
            functools.partial(
                allowed_file_tags_validator,
                allowed_tags={EssayFile.FILE_TAG},
            ),
        ],
    ),
    "purpose/essays_bg": DirectoryValidators(
        validators=[
            no_root_file_validator,
            no_subdirectories_validator,
            functools.partial(
                allowed_file_tags_validator,
                allowed_tags={EssayFile.FILE_TAG},
            ),
        ],
    ),
    # Thoughts and notebooks
    "thoughts": DirectoryValidators(
        validators=[
            no_root_file_validator,
            yarly_directory_current_year_validator,
            yearly_directory_subdirectories_validator,
            functools.partial(
                allowed_file_tags_validator,
                allowed_tags={ThoughtsFile.FILE_TAG},
            ),
        ],
        subdirectory_validators=[
            no_root_file_validator,
            no_subdirectories_validator,
            yearly_directory_parent_year_validator,
        ],
    ),
    # Studies
    "studies": DirectoryValidators(
        validators=[
            root_file_validator,
            only_root_file_validator,
        ],
        subdirectory_validators=[
            root_file_validator,
            functools.partial(
                allowed_file_tags_validator,
                allowed_tags={StudyFile.FILE_TAG},
            ),
        ],
    ),
    # Archive
    "archive": DirectoryValidators(
        validators=[
            archive_validator,
            no_root_file_validator,
            notes_directory_validator,
        ],
        apply_validators_to_subdirectories=True,
    ),
}

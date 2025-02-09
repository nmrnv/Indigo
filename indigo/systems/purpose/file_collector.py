import functools
import os
import typing as t
from copy import copy
from dataclasses import dataclass
from pathlib import Path

from indigo.config import Config
from indigo.models.base import Error
from indigo.models.files import File, FileError
from indigo.models.sections import SectionError
from indigo.systems.purpose.file_validators import *
from indigo.systems.purpose.files import (
    EssayFile,
    RecordedFile,
    StudyFile,
    ThoughtsFile,
)
from indigo.systems.purpose.models import FileRecord


@dataclass
class FileCollectorResult:
    records: t.Sequence[FileRecord]
    errors: t.Sequence[str]


class FileCollectorError(Error): ...


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


class FileCollector:
    def __init__(self):
        self.router = Config.router
        self.root_directory_validators = DirectoryValidators(
            validators=[only_root_file_validator],
        )
        self.default_directory_validators = DirectoryValidators(
            validators=[
                root_file_validator,
                notes_directory_validator,
            ],
            apply_validators_to_subdirectories=True,
        )
        self.directory_validators = DIRECTORY_VALIDATORS

    def relative_to_root(self, path: Path) -> Path:
        return path.relative_to(self.router.notes_directory)

    def collect_files(self, location: Path) -> FileCollectorResult:
        all_records: t.List[FileRecord] = []
        all_errors: t.List[str] = []

        for root, subdirectories, files_ in os.walk(location.as_posix()):
            walked_directory = Path(root)
            filepaths: t.List[Path] = []
            file_records: t.List[FileRecord] = []
            file_tags: t.List[str] = []
            errors: t.List[str] = []

            for file in files_:
                filepath = walked_directory / file
                filepaths.append(filepath)
                relative_path = self.relative_to_root(filepath)

                if filepath.name == ".DS_Store":
                    os.remove(filepath.as_posix())

                try:
                    file = File.match(filepath)
                    file_tags.append(file.FILE_TAG)
                    file.parse()
                    if isinstance(file, RecordedFile):
                        file_records.append(file.record)
                except (FileError, SectionError) as error:
                    errors.append(
                        f"{relative_path.as_posix()!r}: "
                        + str(error).removesuffix(".")
                    )

            directory = Directory(
                path=walked_directory,
                subdirectories=[
                    walked_directory / subdirectory
                    for subdirectory in subdirectories
                ],
                filepaths=filepaths,
                file_records=file_records,
                file_tags=file_tags,
                errors=errors,
            )
            self._run_validators(directory)

            all_records.extend(directory.file_records)
            all_errors.extend(directory.errors)

        return FileCollectorResult(
            records=all_records if not all_errors else [],
            errors=all_errors,
        )

    def _run_validators(self, directory: Directory):
        validators: DirectoryValidators | None = None
        are_child_validators = False
        parts = self.relative_to_root(directory.path).parts
        parts_count = len(parts)

        if not parts:
            validators = self.root_directory_validators
        else:
            while parts:
                joined_parts = "/".join(parts)
                if validators := self.directory_validators.get(
                    joined_parts
                ):
                    are_child_validators = len(parts) != parts_count
                    break
                parts = parts[:-1]
        if not validators:
            validators = self.default_directory_validators
        assert validators

        for validator in (
            validators.validators
            if not are_child_validators
            else validators.subdirectory_validators
        ):
            validator(directory)

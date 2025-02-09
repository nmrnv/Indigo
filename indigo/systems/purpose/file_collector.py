import os
import typing as t
from dataclasses import dataclass
from pathlib import Path

from librum.files import File, FileError
from librum.sections import SectionError

from indigo.base import Error
from indigo.config import Config
from indigo.systems.purpose import directory_validators
from indigo.systems.purpose.directory_validators import (
    DIRECTORY_VALIDATORS,
    DirectoryValidators,
)
from indigo.systems.purpose.files import RecordedFile
from indigo.systems.purpose.models import Directory, FileRecord


@dataclass
class FileCollectorResult:
    records: t.Sequence[FileRecord]
    errors: t.Sequence[str]


class FileCollectorError(Error): ...


class FileCollector:
    def __init__(self):
        self.router = Config.router
        self.root_directory_validators = DirectoryValidators(
            validators=[directory_validators.only_root_file_validator],
        )
        self.default_directory_validators = DirectoryValidators(
            validators=[
                directory_validators.root_file_validator,
                directory_validators.notes_directory_validator,
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
                location=walked_directory,
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

import typing as t
from pathlib import Path

from indigo.config import Config
from indigo.models.base import ID
from indigo.models.files import File, FileError
from indigo.models.sections import SectionError
from indigo.systems.purpose.file_collector import FileCollector
from indigo.systems.purpose.files import EssayFile, RecordedFile
from indigo.systems.purpose.models import FileRecord
from indigo.systems.system import System
from indigo.tools.linker import Linker
from indigo.tools.typer import Typer


class MetadataKeys:
    ESSAYS_COUNT = "essays_count"


class PurposeSystem(System):
    def _on_start(self): ...

    def __init__(self):
        super().__init__()
        self.router = Config.router
        self.collector = FileCollector()

    @System.ask("collect")
    def _collect_file(self, record: FileRecord):
        Typer.header("Collecting file…")
        file = File.match(record.path)
        try:
            file.parse()
        except (FileError, SectionError) as e:
            Typer.body(
                f"{file.name}: Collection unsuccessful. \nFailed with"
                f" error: {e}."
            )
            return
        if not isinstance(file, RecordedFile):
            Typer.body(
                "File is valid, but was not collected as it is not a"
                " RecordedFile."
            )
            return
        self.database.save(file.record)
        Typer.body("File collected.")

    @System.ask("collect subject")
    def _collect_subject_files(self, subject: str):
        subject = subject  # validate subject and get the right folder
        Typer.header(f"Collecting {subject} files…", with_separator=True)
        if not (
            file_records := self._collect_files(self.router.notes_directory)
        ):
            return

    @System.ask("collect all")
    def _collect_all_files(self):
        Typer.header("Collecting files…", with_separator=True)
        if not (
            file_records := self._collect_files(self.router.notes_directory)
        ):
            return
        for title, records in [
            ("Saved", file_records[0]),
            ("Updated", file_records[1]),
            ("Deleted", file_records[2]),
        ]:
            colon = ":" if records else ""
            Typer.list(
                title=f"– {len(records)} {title}{colon}",
                items=[
                    f"{record.title} ({self.collector.relative_to_root(record.path)})"
                    for record in records
                ],
                enumerated=False,
                with_separator=False,
            )
        Typer.body(f"– {len(file_records[3])} Unchanged")

    def _collect_files(
        self, directory: Path
    ) -> t.Tuple[t.Sequence[FileRecord], ...]:
        result = self.collector.collect_files(directory)
        if result.errors:
            with open(Config.router.file_errors_log, "w+") as file:
                for index, error in enumerate(result.errors):
                    file.write(f"{index + 1}. {error}\n–––\n")

            Typer.body(f"Errors: {len(result.errors)}")
            Typer.body(
                "Cannot collect files before all errors are addressed."
            )
            return ()
        if not result.records:
            Typer.body("No files found.")
            return ()
        Typer.body(f"{len(result.records)} files collected.")
        return self.database.save_update_delete(FileRecord, result.records)

    @System.ask("ls essay")
    def _list_essays(self):
        Typer.header("Listing essays…")
        # What about files not collected?
        # I need to check the overhead.
        essays = self.database.list(
            cls=FileRecord,
            predicate=lambda fr: fr.file_tag == EssayFile.FILE_TAG,
        )
        if not essays:
            Typer.body("There are no essays.")
            return
        essays.sort(key=lambda essay: essay.created_at)
        Typer.list([essay.title for essay in essays])
        Linker.link(FileRecord, [essay.id_ for essay in essays])

    @System.ask("export essay")
    def _export_essay(self, id_: ID): ...

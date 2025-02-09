import abc
import typing as t
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from indigo.models.files import File, FileError, SectionDefinition
from indigo.models.patterns import NEW_LINE, SEPARATOR
from indigo.models.sections import Section, SectionPriority
from indigo.systems.purpose.models import (
    FileRecord,
    Note,
    Paragraph,
    Quote,
    Tag,
    Thought,
)
from indigo.systems.purpose.sections import (
    DiaryEntrySection,
    DiaryHeaderSection,
    DraftSection,
    ExcerptSection,
    FreeTextSection,
    HeaderSection,
    NoteSection,
    ParagraphSection,
    PrimaryIdeasSection,
    PurposeSection,
    QuoteSection,
    ReferencesSection,
    ThoughtSection,
    ThoughtsHeaderSection,
)
from indigo.utils import date_utils


class RecordedFile(File, abc.ABC):
    record: FileRecord


class DatedRecordedFile(RecordedFile, abc.ABC):
    date_: datetime

    def setup(
        self,
        specifier: str,
        date_: datetime,
        tags: t.Optional[t.Sequence[Tag]] = None,
    ):
        self.date_ = date_
        month = (
            f"0{date_.month}"
            if len(str(date_.month)) == 1
            else str(date_.month)
        )
        expected_filename = f"{date_.year}.{month}_{specifier}.md"
        if self.path.name != expected_filename:
            raise FileError(
                f"DatedRecordedFile: Filename {self.path.name!r} "
                f"does not match the header-derived {expected_filename!r}."
            )

        record_name = f"{date_.year}.{month} {specifier}"
        self.record = FileRecord(
            file_tag=self.FILE_TAG,
            path=self.path,
            title=record_name,
            tags=tags or [],
        )


class NoteFile(RecordedFile):
    FILE_TAG = "note_file"
    SECTION_DEFINITIONS = [
        SectionDefinition(HeaderSection),
        SectionDefinition(NoteSection, count=-1),
    ]

    title: str
    notes: t.List[Note]
    tags: t.Sequence[Tag]

    def __init__(self, path: Path):
        super().__init__(path)
        self.notes = []
        self.tags = []

    def on_match(self, section: Section):
        if isinstance(section, HeaderSection):
            self.title = section.title
            self.tags = section.tags
            self.record = FileRecord(
                file_tag=self.FILE_TAG,
                path=self.path,
                title=self.title,
                tags=self.tags,
            )
        elif isinstance(section, NoteSection):
            if any([tag in self.tags for tag in section.tags]):
                raise FileError(
                    "NoteFile: Notes cannot duplicate file tags."
                )
            note = Note(
                title=section.title,
                text=section.text,
                tags=[*self.tags, *section.tags],
                file_id=self.record.id_,
            )
            self.notes.append(note)

    def on_complete(self):
        note_titles = set()
        for note in self.notes:
            if note.title in note_titles:
                raise FileError(f"NoteFile: Duplicate note {note.title!r}.")
            note_titles.add(note.title)


class RootFile(NoteFile):
    FILE_TAG = "root_file"

    def on_match(self, section: Section):
        if isinstance(section, HeaderSection):
            file_name = (
                self.path.name.removeprefix("_")
                .removesuffix(".md")
                .capitalize()
                .replace("_", " ")
            )
            if section.title != file_name.capitalize():
                raise FileError(
                    f"RootFile: Header section title {section.title!r} "
                    f"does not match file name {file_name!r}."
                )
        super().on_match(section)


class DiaryFile(DatedRecordedFile):
    FILE_TAG = "diary_file"
    SECTION_DEFINITIONS = [
        SectionDefinition(DiaryHeaderSection),
        SectionDefinition(DiaryEntrySection, count=-1),
    ]

    _entry_dates: t.List[datetime]

    def __init__(self, path: Path):
        super().__init__(path)
        self._entry_dates = []

    def on_match(self, section: Section):
        if isinstance(section, DiaryHeaderSection):
            self.setup("Diary", section.date_)
        elif isinstance(section, DiaryEntrySection):
            if not self.date_.month == section.month:
                raise FileError(
                    "DiaryFile: Entry month"
                    f" {date_utils.Month.from_index(section.month).capitalize()} "
                    "does not match file month"
                    f" {date_utils.Month.from_index(self.date_.month).capitalize()}."
                )
            try:
                entry_date = self.date_.replace(day=section.day)
            except ValueError:
                raise FileError(
                    f"DiaryFile: Invalid entry day {section.day}."
                )
            if entry_date in self._entry_dates:
                raise FileError(
                    "DiaryFile: Cannot have two entries for"
                    f" {date_utils.date_str(entry_date, worded=False)}."
                )
            if self._entry_dates and self._entry_dates[-1] > entry_date:
                raise FileError(
                    "DiaryFile: Entry on date"
                    f" {date_utils.date_str(entry_date, worded=False)} "
                    "should not be listed before the one on "
                    f"{date_utils.date_str(self._entry_dates[-1], worded=False)}."
                )
            expected_weekday = entry_date.weekday()
            if not expected_weekday == section.weekday:
                weekday = date_utils.Weekday.from_index(section.weekday)
                expected_weekday = date_utils.Weekday.from_index(
                    expected_weekday
                )
                raise FileError(
                    f"DiaryFile: Invalid weekday {weekday.capitalize()} for"
                    " entry on"
                    f" {date_utils.date_str(entry_date, worded=False)}."
                    f" Should be {expected_weekday.capitalize()}."
                )
            self._entry_dates.append(entry_date)


class ThoughtsFile(DatedRecordedFile):
    FILE_TAG = "thoughts_file"
    SECTION_DEFINITIONS = [
        SectionDefinition(ThoughtsHeaderSection),
        SectionDefinition(ThoughtSection, count=-1),
    ]

    thoughts: t.List[Thought]

    def __init__(self, path: Path):
        super().__init__(path)
        self.thoughts = []

    def on_match(self, section: Section):
        if isinstance(section, ThoughtsHeaderSection):
            self.setup("Thoughts", section.date_)
        elif isinstance(section, ThoughtSection):
            thought = Thought(
                date=self.date_,
                text=section.text,
                tags=section.tags,
                file_id=self.record.id_,
            )
            self.thoughts.append(thought)

    def on_complete(self):
        thoughts = set()
        for thought in self.thoughts:
            if thought.text in thoughts:
                raise FileError(
                    "ThoughtsFile: Cannot have duplicate thoughts."
                )
            thoughts.add(thought.text)


class EssayFile(RecordedFile):
    FILE_TAG = "essay_file"
    SECTION_DEFINITIONS = [
        SectionDefinition(HeaderSection),
        SectionDefinition(PurposeSection),
        SectionDefinition(NoteSection, count=-1, optional=True),
        SectionDefinition(
            section=DraftSection,
            subsections=[
                SectionDefinition(ParagraphSection, count=-1),
                SectionDefinition(
                    ReferencesSection,
                    priority=SectionPriority.HIGHER,
                    optional=True,
                ),
            ],
            separator_count=2,
        ),
    ]

    number: int
    tags: t.Sequence[Tag]
    purpose: str
    notes: t.List[Note]

    title: str
    paragraphs: t.List[Paragraph]
    references: t.Optional[t.List[str]] = None

    @classmethod
    def create(cls, path: Path, title: str):
        with open(path.as_posix(), mode="w") as file:
            lines = [
                f"## {title}",
                f"`[{cls.FILE_TAG}]`",
                SEPARATOR,
                "# Purpose and key points",
                "...",
                SEPARATOR,
                "# Outline",
                "- Paragraph I",
                SEPARATOR,
                SEPARATOR,
                "## Draft",
                SEPARATOR,
                "# Paragraph I",
                "...\n",
            ]
            file.writelines("\n".join(lines))

    def __init__(self, path: Path):
        super().__init__(path)
        self.tags = []
        self.notes = []
        self.paragraphs = []

    def on_match(self, section: Section):
        if isinstance(section, HeaderSection):
            self.title = section.title
            self.tags = section.tags

        elif isinstance(section, PurposeSection):
            self.purpose = section.text
            self.record = FileRecord(
                file_tag=self.FILE_TAG,
                path=self.path,
                title=self.title,
                synopsis=self.purpose,
                tags=self.tags,
            )

        elif isinstance(section, NoteSection):
            note = Note(
                title=section.title,
                text=section.text,
                file_id=self.record.id_,
            )
            self.notes.append(note)

        elif isinstance(section, ParagraphSection):
            paragraph = Paragraph(
                title=section.title,
                text=section.text,
                file_id=self.record.id_,
            )
            self.paragraphs.append(paragraph)

        elif isinstance(section, ReferencesSection):
            self.references = section.references

    def on_complete(self):
        # TODO: Validate no duplicates
        ...


class StudyFile(RecordedFile):
    FILE_TAG = "study_file"
    INLINE_SECTION_DEFINITIONS = [
        SectionDefinition(
            FreeTextSection,
            priority=SectionPriority.INTERRUPTING,
            optional=True,
            ordered=False,
            count=-1,
        ),
        SectionDefinition(
            QuoteSection, optional=True, ordered=False, count=-1
        ),
        SectionDefinition(
            ExcerptSection, optional=True, ordered=False, count=-1
        ),
    ]
    NOTE_DEFINITION = [
        SectionDefinition(
            NoteSection,
            subsections=deepcopy(INLINE_SECTION_DEFINITIONS),
            count=-1,
            ordered=False,
            optional=True,
        ),
    ]
    SECTION_DEFINITIONS = [
        SectionDefinition(HeaderSection),
        *deepcopy(NOTE_DEFINITION),
        SectionDefinition(
            PrimaryIdeasSection,
            subsections=[],
            separator_count=2,
        ),
    ]

    title: str
    tags: t.Sequence[Tag]

    notes: t.List[Note]
    quotes: t.List[Quote]

    def __init__(self, path: Path):
        super().__init__(path)
        self.notes = []
        self.quotes = []

    def on_match(self, section: Section):
        if isinstance(section, HeaderSection):
            self.title = section.title
            self.tags = section.tags
            self.record = FileRecord(
                file_tag=self.FILE_TAG,
                path=self.path,
                title=self.title,
                tags=self.tags,
            )

        elif isinstance(section, NoteSection):
            if any([tag in self.tags for tag in section.tags]):
                raise FileError(
                    "StudyFile: Notes cannot duplicate file tags."
                )
            note = Note(
                title=section.title,
                text=section.text,
                tags=[*self.tags, *section.tags],
                file_id=self.record.id_,
            )
            self.notes.append(note)

        elif isinstance(section, ExcerptSection):
            last_note = self.notes[-1]
            separator = NEW_LINE + NEW_LINE
            last_note.text += separator + "Excerpt: " + section.excerpt

        elif isinstance(section, QuoteSection):
            quote = Quote(
                text=section.quote,
                author=section.author,
                page=section.page,
                note_id=self.notes[-1].id_,
                file_id=self.record.id_,
            )
            self.quotes.append(quote)

        elif isinstance(section, FreeTextSection):
            last_note = self.notes[-1]
            last_note.text += NEW_LINE + NEW_LINE
            last_note.text += section.text

    def on_complete(self):
        note_titles = set()
        for note in self.notes:
            if note.title in note_titles:
                raise FileError(
                    f"StudyFile: Duplicate note {note.title!r}."
                )
            note_titles.add(note.title)

import abc
import re
import typing as t
from datetime import datetime

from librum.patterns import (
    RE_ANY_TEXT_EXCEPT_NEW_LINE_PATTERN,
    RE_ANY_TEXT_PATTERN,
    RE_DAY_PATTERN,
    RE_FILE_TITLE_PATTERN,
    RE_MONTH_NAME_PATTERN,
    RE_MONTH_PATTERN,
    RE_QUESTION_PATTERN,
    RE_SEPARATOR_PATTERN,
    RE_TAG_PATTERN,
    RE_TAGS_PATTERN,
    RE_TAGS_PATTERN_WITH_PAGES,
    RE_TITLE_PATTERN,
    RE_WEEKDAY_PATTERN,
    RE_YEAR_PATTERN,
)
from librum.sections import (
    Line,
    LineDefinition,
    Section,
    SectionError,
)

from indigo.systems.purpose.models import Tag
from indigo.utils import date_utils


class TextSection(Section, abc.ABC):
    _lines: t.List[str]

    def __init__(self, starting_line: Line):
        self._lines = []
        super().__init__(starting_line=starting_line)

    @property
    def text(self) -> str:
        if not self._lines:
            return ""
        return "\n".join(self._lines).strip()

    def add_line(self, line: str):
        self._lines.append(line)


class TitledTextSection(TextSection, abc.ABC):
    title: str

    def match(self, definition: LineDefinition, match: re.Match):
        if definition == self.LINE_DEFINITIONS[0]:
            self.title = match.groups()[0]

        elif definition == self.LINE_DEFINITIONS[1]:
            line = match.groups()[0]
            self.add_line(line)


class PredefinedTitledSection(Section, abc.ABC):
    LINE_DEFINITIONS = [LineDefinition("...")]
    TITLE_PATTERN: str = "..."

    def __init_subclass__(cls, *_, **__):
        cls.LINE_DEFINITIONS = [LineDefinition(cls.TITLE_PATTERN)]
        super().__init_subclass__(cls)

    def on_match(self, definition: LineDefinition, match: re.Match): ...


class PredefinedTitledTextSection(
    PredefinedTitledSection, TextSection, abc.ABC
):
    LINE_DEFINITIONS = []
    OPTIONAL_TEXT: bool = False

    def __init_subclass__(cls, *_, **__):
        super().__init_subclass__()
        cls.LINE_DEFINITIONS = [
            *cls.LINE_DEFINITIONS,
            LineDefinition(RE_ANY_TEXT_PATTERN, count=-1),
        ]
        cls.LINE_DEFINITIONS[1].optional = cls.OPTIONAL_TEXT

    def on_match(self, definition: LineDefinition, match: re.Match):
        if definition == self.LINE_DEFINITIONS[1]:
            line = match.groups()[0]
            self.add_line(line)


class TaggedSection(Section, abc.ABC):
    tags: t.Sequence[Tag]

    def __init__(self, starting_line: Line):
        self.tags = []
        super().__init__(starting_line)

    def match_tags(self, match: re.Match):
        self.tags = re.findall(RE_TAG_PATTERN, match.string)
        if len(self.tags) != len(set(self.tags)):
            raise SectionError(f"{self.name}: Cannot have duplicate tags.")


class TitledTaggedTextSection(TitledTextSection, TaggedSection, abc.ABC):
    def match(self, definition: LineDefinition, match: re.Match):
        if definition == self.LINE_DEFINITIONS[0]:
            self.title = match.groups()[0]

        elif definition == self.LINE_DEFINITIONS[1]:
            self.match_tags(match)

        elif definition == self.LINE_DEFINITIONS[2]:
            line = match.groups()[0]
            self.add_line(line)


class HeaderSection(Section):
    LINE_DEFINITIONS = [
        LineDefinition(RE_FILE_TITLE_PATTERN),
        LineDefinition(RE_TAGS_PATTERN),
    ]

    title: str
    tags: t.Sequence[Tag]

    def on_match(self, definition: LineDefinition, match: re.Match):
        if definition == self.LINE_DEFINITIONS[0]:
            self.title = match.groups()[0]

        elif definition == self.LINE_DEFINITIONS[1]:
            # We are skipping the file type tag, hence [1:]
            self.tags = re.findall(RE_TAG_PATTERN, match.string)[1:]
            if len(self.tags) != len(set(self.tags)):
                raise SectionError("Cannot have duplicate tags.")


class PrimaryIdeasSection(PredefinedTitledSection):
    TITLE_PATTERN = r"^## Primary Ideas$"


class PageableSection(TitledTaggedTextSection):
    LINE_DEFINITIONS = [LineDefinition("...")]
    pages: t.Sequence[str]

    def on_match(self, definition: LineDefinition, match: re.Match):
        if definition == self.LINE_DEFINITIONS[1]:
            self.pages = []
        super().match(definition, match)


class NoteSection(PageableSection):
    LINE_DEFINITIONS = [
        LineDefinition(rf"^# ({RE_TITLE_PATTERN})$"),
        LineDefinition(RE_TAGS_PATTERN_WITH_PAGES, optional=True),
        LineDefinition(RE_ANY_TEXT_PATTERN, count=-1),
    ]


class FreeTextSection(TextSection):
    LINE_DEFINITIONS = [
        LineDefinition(RE_ANY_TEXT_EXCEPT_NEW_LINE_PATTERN, count=-1)
    ]
    END_PATTERN = RE_SEPARATOR_PATTERN

    def on_match(self, definition: LineDefinition, match: re.Match):
        line = match.groups()[0]
        self.add_line(line)


class ExcerptSection(Section):
    LINE_DEFINITIONS = [LineDefinition(r"^E\) ([A-Z].+)$")]

    excerpt: str

    def on_match(self, definition: LineDefinition, match: re.Match):
        self.excerpt = match.groups()[0]


class QuoteSection(Section):
    LINE_DEFINITIONS = [
        LineDefinition(r'^Q\) "([A-Z].+)", ([a-zA-Z ]+), page ([0-9]+)$'),
    ]

    quote: str
    author: str
    page: str

    def on_match(self, definition: LineDefinition, match: re.Match):
        groups = match.groups()
        (self.quote, self.author, self.page) = groups


class PurposeSection(PredefinedTitledTextSection):
    TITLE_PATTERN = r"^# Purpose and key points$"


class DraftSection(PredefinedTitledTextSection):
    TITLE_PATTERN = r"^## Draft$"
    OPTIONAL_TEXT = True


class ParagraphSection(TitledTextSection):
    LINE_DEFINITIONS = [
        LineDefinition(rf"^# ({RE_TITLE_PATTERN}|{RE_QUESTION_PATTERN})$"),
        LineDefinition(RE_ANY_TEXT_PATTERN, count=-1),
    ]

    def on_match(self, definition: LineDefinition, match: re.Match):
        super().match(definition, match)


class ReferencesSection(Section):
    LINE_DEFINITIONS = [
        LineDefinition(r"^# References$"),
        LineDefinition(r"^([\d]+). ([A-Z].+)", count=-1),
    ]

    references: t.List[str]

    def __init__(self, starting_line: Line):
        self.references = []
        super().__init__(starting_line)

    def on_match(self, definition: LineDefinition, match: re.Match):
        if definition == self.LINE_DEFINITIONS[1]:
            groups = match.groups()
            number, reference = int(groups[0]), groups[1]
            if not number - 1 == len(self.references):
                raise SectionError(
                    f"ReferencesSection: Invalid number {number} for"
                    f" reference {reference!r}. Should be"
                    f" {len(self.references) + 1}."
                )
            self.references.append(reference)


class ThoughtsHeaderSection(Section):
    LINE_DEFINITIONS = [
        LineDefinition(
            rf"^## {RE_YEAR_PATTERN}.{RE_MONTH_PATTERN} Thoughts$"
        ),
        LineDefinition(RE_TAGS_PATTERN),
    ]

    date_: datetime

    def on_match(self, definition: LineDefinition, match: re.Match):
        if definition == self.LINE_DEFINITIONS[0]:
            groups = match.groups()
            first_of_month_string = f"01/{groups[1]}/{groups[0]}"
            self.date_ = date_utils.date_from_str(first_of_month_string)

        elif definition == self.LINE_DEFINITIONS[1]:
            tags = re.findall(RE_TAG_PATTERN, match.string)
            if len(tags) != 1:
                raise SectionError("Tags must only contain the file one.")


class ThoughtSection(TextSection, TaggedSection):
    LINE_DEFINITIONS = [
        LineDefinition("([A-Z].+)", count=-1),
        LineDefinition(RE_TAGS_PATTERN),
    ]

    def on_match(self, definition: LineDefinition, match: re.Match):
        if definition == self.LINE_DEFINITIONS[0]:
            line = match.groups()[0]
            self.add_line(line)

        elif definition == self.LINE_DEFINITIONS[1]:
            self.match_tags(match)


class DiaryHeaderSection(Section):
    LINE_DEFINITIONS = [
        LineDefinition(rf"^## {RE_YEAR_PATTERN}.{RE_MONTH_PATTERN} Diary$"),
        LineDefinition(RE_TAGS_PATTERN),
    ]

    date_: datetime

    def on_match(self, definition: LineDefinition, match: re.Match):
        if definition == self.LINE_DEFINITIONS[0]:
            groups = match.groups()
            first_of_month_string = f"01/{groups[1]}/{groups[0]}"
            self.date_ = date_utils.date_from_str(first_of_month_string)

        elif definition == self.LINE_DEFINITIONS[1]:
            tags = re.findall(RE_TAG_PATTERN, match.string)
            if len(tags) != 1:
                raise SectionError(
                    "DiaryHeaderSection: Cannot contain other than the file"
                    " tag."
                )


class DiaryEntrySection(TextSection):
    LINE_DEFINITIONS = [
        LineDefinition(
            rf"^# {RE_DAY_PATTERN}(?:st|nd|rd|th) of "
            rf"{RE_MONTH_NAME_PATTERN}, {RE_WEEKDAY_PATTERN}$"
        ),
        LineDefinition(RE_ANY_TEXT_PATTERN, count=-1),
    ]

    day: int
    month: int
    weekday: int

    def on_match(self, definition: LineDefinition, match: re.Match):
        if definition == self.LINE_DEFINITIONS[0]:
            groups = match.groups()
            self.day = int(groups[0])
            self.month = date_utils.Month(groups[1].lower()).index_
            self.weekday = date_utils.Weekday(groups[2].lower()).index_

        elif definition == self.LINE_DEFINITIONS[1]:
            line = match.groups()[0]
            self.add_line(line)

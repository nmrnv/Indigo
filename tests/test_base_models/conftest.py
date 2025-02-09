import typing as t

from indigo.models.files import File
from indigo.models.patterns import RE_TAGS_PATTERN
from indigo.models.sections import LineDefinition, Section


class File_(File):
    matched_sections = []
    on_match_calls = 0
    on_complete_calls = 0

    def __init__(self, *args, **kwargs):
        self.matched_sections = []
        super().__init__(*args, **kwargs)

    def match_(self, section: Section):
        self.matched_sections.append(section.__class__)
        self.on_match_calls += 1

    def on_complete(self):
        self.on_complete_calls += 1


class Section_(Section):
    LINE_DEFINITIONS = [LineDefinition("Header")]

    def on_match(self, *_):
        pass


class HeaderSection(Section_):
    LINE_DEFINITIONS = [
        LineDefinition("Header"),
        LineDefinition(RE_TAGS_PATTERN),
    ]


class BodySection(Section_):
    LINE_DEFINITIONS = [LineDefinition("Body")]


class GroupSection(Section_):
    LINE_DEFINITIONS = [LineDefinition("Group")]


class NoteSection(Section_):
    LINE_DEFINITIONS = [LineDefinition("Note")]


class CommentSection(Section_):
    LINE_DEFINITIONS = [LineDefinition("Comment")]


class FooterSection(Section_):
    LINE_DEFINITIONS = [LineDefinition("Footer")]


def assert_calls(
    file: File_,
    number_of_sections: int,
    number_of_lines: t.Optional[int] = None,
):
    assert file.number_of_lines == number_of_lines or number_of_sections * 2
    assert file.on_match_calls == number_of_sections
    assert file.on_complete_calls == 1

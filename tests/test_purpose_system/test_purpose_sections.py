import pytest
from freezegun import freeze_time

from indigo.models.patterns import SEPARATOR
from indigo.models.sections import Line, SectionError
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
    QuestionSection,
    QuoteSection,
    ReferencesSection,
    RemarksSection,
    SecondaryIdeasSection,
    SynopsisSection,
    ThoughtSection,
    ThoughtsHeaderSection,
)
from indigo.utils import date_utils
from tests.test_base_models.test_sections import (
    make_lines,
    make_section,
)


def test_header_section():
    # Given
    title = "Title: with, al1–possible sym-bols"
    lines = make_lines(
        f"## {title}",
        "`[study_file][philosophy][metaphysics]`",
    )

    # When
    header_section = make_section(HeaderSection, lines)

    # Then
    assert header_section.completed
    assert header_section.title == title
    assert header_section.tags == ["philosophy", "metaphysics"]


@pytest.mark.parametrize(
    "invalid_title",
    (
        "Title ending with question?",
        "Title ending with full-stop.",
        "Title ending with exclamation-mark!",
        " Starting with space",
        "starting with lowercase letter",
        "Containing invalid@symbol",
        "Containing new \n line",
        "Containing \t tab",
    ),
)
def test_header_section_with_invalid_symbols(invalid_title: str):
    # Given
    line = Line(index=0, text=f"# {invalid_title}")

    # Then
    with pytest.raises(
        SectionError,
        match="HeaderSection: Invalid line 0:",
    ):
        # When
        HeaderSection(line)


def test_synopsis_section():
    # Given
    lines = make_lines(
        "# Synopsis",
        "First line",
        "Second line",
    )

    # When
    synopsis_section = make_section(SynopsisSection, lines)

    # Then
    assert synopsis_section.text == "First line\nSecond line"
    assert not synopsis_section.completed

    # When
    synopsis_section.on_end()

    # Then
    assert synopsis_section.text == "First line\nSecond line"
    assert synopsis_section.completed


@pytest.mark.parametrize(
    "cls, title",
    [
        (PrimaryIdeasSection, "Primary Ideas"),
        (SecondaryIdeasSection, "Secondary Ideas"),
        (RemarksSection, "Remarks"),
    ],
)
def test_study_notes_rank_sections(cls, title: str):
    # Given
    line = Line(index=0, text=f"## {title}")

    # When
    section = cls(starting_line=line)

    # Then
    assert section.completed


@pytest.mark.parametrize(
    "title",
    (
        "Title",
        "Title with numb3r",
        "Title, with comma",
        "Title with: colon",
        "Title with - two – dashes",
        "Title: with, al1 – possible: sym-bols",
    ),
)
def test_note_text_section(title: str):
    # Given
    lines = make_lines(
        f"# {title}",
        "`[philosophy][metaphysics]`",
        "Text line",
        "Second text line",
        SEPARATOR,
    )

    # When
    tagged_text_section = make_section(NoteSection, lines)
    tagged_text_section.on_end()

    # Then
    assert tagged_text_section.completed
    assert tagged_text_section.title == title
    assert tagged_text_section.tags == ["philosophy", "metaphysics"]
    assert tagged_text_section.text == "Text line\nSecond text line"


@pytest.mark.parametrize(
    "invalid_title",
    (
        "Title ending with question?",
        "Title ending with full-stop.",
        "Title ending with exclamation-mark!",
        " Starting with space",
        "starting with lowercase letter",
        "Containing invalid@symbol",
        "Containing new \n line",
        "Containing \t tab",
    ),
)
def test_note_section_with_invalid_symbols(invalid_title: str):
    # Given
    line = Line(index=0, text=f"# {invalid_title}")

    # Then
    with pytest.raises(
        SectionError,
        match="NoteSection: Invalid line 0:",
    ):
        # When
        NoteSection(line)


def test_note_section_without_tags():
    # Given
    lines = make_lines(
        "# Title",
        "Text line",
    )

    # When
    section = make_section(NoteSection, lines)
    section.on_end()

    # Then
    assert section.completed
    assert section.title == "Title"
    assert section.tags == []
    assert section.text == "Text line"


def test_note_section_without_text():
    # Given
    lines = make_lines("# Title", "`[philosophy][metaphysics]`")
    section = make_section(NoteSection, lines, until_index=2)

    # Then
    with pytest.raises(
        SectionError,
        match="End of section reached before section was completed.",
    ):
        # When
        section.on_end()


def test_note_section_without_tags_and_text():
    # Given
    line = Line(index=0, text="# Title")
    section = NoteSection(line)

    # Then
    with pytest.raises(
        SectionError,
        match="End of section reached before section was completed.",
    ):
        # When
        section.on_end()


def test_note_section_failure_with_duplicate_tags():
    # Given
    lines = make_lines(
        "# Title",
        "`[duplicate][duplicate]`",
    )
    section = NoteSection(starting_line=lines[0])

    # Then
    with pytest.raises(
        SectionError,
        match="NoteSection: Cannot have duplicate tags.",
    ):
        # When
        section.consume_line(lines[1])


def test_question_section():
    # Given
    question = "Question: with, al1 – possible: sym-bols?"
    lines = make_lines(
        f"# {question}",
        "Question text",
        "Further text",
    )

    # When
    question_section = make_section(QuestionSection, lines)
    question_section.on_end()

    # Then
    assert question_section.completed
    assert question_section.title == question
    assert question_section.text == "Question text\nFurther text"


@pytest.mark.parametrize(
    "invalid_question",
    (
        "Not ending with question mark.",
        "Not ending with question mark!",
        " Starting with space",
        "starting with lowercase letter",
        "Containing invalid@symbol",
        "Containing new \n line",
        "Containing \t tab",
    ),
)
def test_question_section_with_invalid_symbols(invalid_question: str):
    # Given
    line = Line(index=0, text=f"# {invalid_question}?")

    # Then
    with pytest.raises(
        SectionError,
        match="QuestionSection: Invalid line 0:",
    ):
        # When
        QuestionSection(line)


def test_question_section_failure_with_duplicate_tags():
    # Given
    lines = make_lines(
        "# Question title?",
        "`[duplicate][duplicate]`",
    )
    section = QuestionSection(starting_line=lines[0])

    # Then
    with pytest.raises(
        SectionError,
        match="QuestionSection: Cannot have duplicate tags.",
    ):
        # When
        section.consume_line(lines[1])


def test_free_text_section():
    # Given
    lines = make_lines(
        "This is a free text",
        "section, on multiple",
        "lines",
    )

    # When
    section = make_section(FreeTextSection, lines)
    section.on_end()

    # Then
    assert section.completed
    assert (
        section.text == "This is a free text\nsection, on multiple\nlines"
    )


def test_excerpt_section():
    # Given
    line = Line(0, "E) This is an excerpt section. On a single line.")

    # When
    section = ExcerptSection(starting_line=line)

    # Then
    assert section.completed
    assert (
        section.excerpt == "This is an excerpt section. On a single line."
    )


def test_quote_section():
    # Given
    line = Line(0, 'Q) "Quote text.", Arthur Schopenhauer, page 15')

    # When
    quote_section = QuoteSection(starting_line=line)

    # Then
    assert quote_section.completed
    assert quote_section.quote == "Quote text."
    assert quote_section.author == "Arthur Schopenhauer"
    assert quote_section.page == "15"


def test_purpose_section():
    # Given
    lines = make_lines(
        "# Purpose and key points",
        "The purpose of this essay",
    )

    # When
    purpose_section = make_section(PurposeSection, lines)

    # Then
    assert purpose_section.text == "The purpose of this essay"
    assert not purpose_section.completed


def test_draft_section():
    # Given
    lines = make_lines("## Draft", "Ideation about title")

    # When
    section = make_section(DraftSection, lines)
    section.on_end()

    # Then
    assert section.completed
    assert section.text == "Ideation about title"


def test_draft_section_without_text():
    # Given
    line = Line(index=0, text="## Draft")

    # When
    section = DraftSection(line)

    # Then
    assert section.has_consumed_all_definitions()
    assert not section.completed


def test_paragraph_section():
    # Given
    title = "Paragraph title: with, al1 – possible: sym-bols"
    lines = make_lines(f"# {title}", "Paragraph text")

    # When
    section = make_section(ParagraphSection, lines)

    # Then
    assert section.title == title
    assert section.text == "Paragraph text"
    assert not section.completed


@pytest.mark.parametrize(
    "invalid_paragraph_title",
    (
        " Starting with space",
        "starting with lowercase letter",
        "Paragraph title ending with full-stop.",
        "Paragraph title ending with exclamation-mark!",
        "Containing invalid@symbol",
        "Containing new \n line",
        "Containing \t tab",
    ),
)
def test_paragraph_section_with_invalid_symbols(
    invalid_paragraph_title: str,
):
    # Given
    line = Line(index=0, text=f"[p] {invalid_paragraph_title}")

    # Then
    with pytest.raises(
        SectionError,
        match="ParagraphSection: Invalid line 0:",
    ):
        # When
        ParagraphSection(line)


def test_references_section():
    # Given
    lines = make_lines(
        "# References",
        "1. Schopenhauer, A. 1819 2nd edition page 123",
        "2. Nietzsche, F. 1883 1st edition page 789",
    )

    # When
    section = make_section(ReferencesSection, lines)

    # Then
    assert not section.completed
    assert section.references == [
        "Schopenhauer, A. 1819 2nd edition page 123",
        "Nietzsche, F. 1883 1st edition page 789",
    ]


def test_references_failure_with_wrong_index():
    # Given
    lines = make_lines(
        "# References",
        "1. Schopenhauer, A. 1819 2nd edition page 123",
        "3. Nietzsche, F. 1883 1st edition page 789",
    )

    # When
    section = make_section(ReferencesSection, lines, until_index=2)

    # Then
    with pytest.raises(
        SectionError,
        match=(
            "ReferencesSection: Invalid number 3 for reference "
            "'Nietzsche, F. 1883 1st edition page 789'. Should be 2."
        ),
    ):
        # When
        section.consume_line(lines[2])


@freeze_time("01/01/2022")
def test_thoughts_header_section():
    # Given
    lines = make_lines("## 2022.01 Thoughts", "`[thoughts_file]`")

    # When
    section = make_section(ThoughtsHeaderSection, lines)

    # Then
    assert section.completed
    assert section.date_ == date_utils.beginning_of_day()


@freeze_time("01/01/2022")
def test_thoughts_header_section_failure_with_more_than_file_tag():
    # Given
    lines = make_lines(
        "## 2022.01 Thoughts",
        "`[thoughts_file][extra_tag]`",
    )
    section = ThoughtsHeaderSection(starting_line=lines[0])

    # Then
    with pytest.raises(
        SectionError,
        match="Tags must only contain the file one.",
    ):
        # When
        section.consume_line(lines[1])


def test_thought_section():
    # Given
    lines = make_lines(
        "Thought on ethics.",
        "`[philosophy][ethics]`",
    )

    # When
    section = make_section(ThoughtSection, lines)

    # Then
    assert section.text == "Thought on ethics."
    assert section.tags == ["philosophy", "ethics"]


def test_thought_section_without_tag_failure():
    # Given
    lines = make_lines(
        "This thought does not have tags",
        SEPARATOR,
    )
    section = ThoughtSection(starting_line=lines[0])

    # Then
    with pytest.raises(
        SectionError,
        match="ThoughtSection: Invalid line 1",
    ):
        # When
        section.consume_line(lines[1])


def test_thought_section_failure_with_duplicate_tags():
    # Given
    lines = make_lines(
        "Thought with duplicate tags",
        "`[duplicate][duplicate]`",
    )
    section = ThoughtSection(starting_line=lines[0])

    # Then
    with pytest.raises(
        SectionError,
        match="ThoughtSection: Cannot have duplicate tags.",
    ):
        # When
        section.consume_line(lines[1])


@freeze_time("01/01/2022")
def test_diary_header_section():
    # Given
    lines = make_lines(
        "## 2022.01 Diary",
        "`[diary_file]`",
    )

    # When
    section = make_section(DiaryHeaderSection, lines)

    # Then
    assert section.completed
    assert section.date_ == date_utils.beginning_of_day()


@freeze_time("01/01/2022")
def test_diary_header_section_contains_more_tags():
    # Given
    lines = make_lines(
        "## 2022.01 Diary",
        "`[diary_file][extra_tag]`",
    )
    header_section = DiaryHeaderSection(starting_line=lines[0])

    # Then
    with pytest.raises(
        SectionError,
        match="DiaryHeaderSection: Cannot contain other than the file tag.",
    ):
        # When
        header_section.consume_line(lines[1])


@freeze_time("01/01/2022")
def test_diary_entry_section():
    # Given
    lines = make_lines(
        "# 3rd of January, Monday",
        "Entry text",
    )

    # When
    section = make_section(DiaryEntrySection, lines)

    # Then
    assert section.day == 3
    assert section.month == 1
    assert section.weekday == 0
    assert not section.completed

import subprocess
from datetime import date
from unittest.mock import MagicMock, call

import pytest
from pytest import MonkeyPatch

from indigo.tools import typer
from indigo.tools.typer import Typer
from indigo.utils import date_utils


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch: MonkeyPatch):
    monkeypatch.setattr(typer, "INDENT", 2)
    monkeypatch.setattr(typer, "WIDTH", 16)


@pytest.fixture
def print_(monkeypatch: MonkeyPatch):
    print_ = MagicMock()
    monkeypatch.setattr(Typer, "print_", print_)
    yield print_


@pytest.mark.parametrize(
    "text, expected",
    [
        ("short text", "  short text"),
        ("very very long text", "  very very long\n    text"),
    ],
)
@pytest.mark.parametrize("with_separator", [True, False])
def test_header(
    text: str, expected: str, with_separator: bool, print_: MagicMock
):
    # When
    Typer.header(text, with_separator)

    # Then
    assert print_.call_args_list[0] == call("")
    assert print_.call_args_list[1] == call(expected)
    if not with_separator:
        assert print_.call_count == 2
    else:
        assert print_.call_args_list[2] == call("")
        assert print_.call_count == 3


@pytest.mark.parametrize(
    "text, expected",
    [
        ("short text", "  short text"),
        ("very very long text", "  very very long\n    text"),
    ],
)
def test_body(text: str, expected: str, print_: MagicMock):
    # When
    Typer.body(text)

    # Then
    assert print_.call_args_list == [call(expected)]


def test_separator(print_: MagicMock):
    # When
    Typer.separator()

    # Then
    assert print_.call_args_list == [call("")]


class TestList:
    @pytest.mark.parametrize(
        "item, expected",
        [
            ("short item", "  {}. short item"),
            ("very long item", "  {}. very long\n    item"),
        ],
    )
    def test_list(self, item: str, expected: str, print_: MagicMock):
        # When
        Typer.list([item, item])

        # Then
        assert print_.call_args_list == [
            call(""),
            call(expected.format(1)),
            call(expected.format(2)),
        ]

    @pytest.mark.parametrize("one_line", [True, False])
    def test_list_non_enumerated(self, print_: MagicMock, one_line: bool):
        # When
        Typer.list(
            ["a", "b"],
            enumerated=False,
            with_separator=False,
            one_line=one_line,
        )

        # Then
        assert print_.call_args_list == [
            call("  – a"),
            call("  – b"),
        ]

    def test_list_with_one_line(self, print_: MagicMock):
        # When
        Typer.list(["a", "b"], with_separator=False, one_line=True)

        # Then
        assert print_.call_args_list == [call("  1.a  2.b")]

    def test_list_with_title(self, print_: MagicMock):
        # When
        Typer.list(["item"], title="title", with_separator=False)

        # Then
        assert print_.call_args_list == [
            call(""),
            call("  title"),
            call("  1. item"),
        ]


class TestInput:
    @pytest.fixture(autouse=True)
    def patch_settings(patch_settings, monkeypatch: MonkeyPatch):
        monkeypatch.setattr(typer, "INDENT", 2)
        monkeypatch.setattr(typer, "WIDTH", 120)

    @pytest.fixture
    def input_(cls, monkeypatch: MonkeyPatch):
        input_ = MagicMock(side_effect=["input", "cancel"])
        monkeypatch.setattr(Typer, "input_", input_)
        yield input_

    @pytest.mark.parametrize("with_separator", [True, False])
    def test_input(
        self, with_separator: bool, input_: MagicMock, print_: MagicMock
    ):
        # When
        result = Typer.input("prompt", with_separator=with_separator)

        # Then
        assert result == "input"
        input_.assert_called_once_with("  prompt ")
        if with_separator:
            assert print_.call_args_list == [call("")]
        else:
            assert not print_.call_args_list

    def test_input_with_validator(self, input_: MagicMock):
        # When
        result = Typer.input("prompt", validator=lambda x: x == "input")

        # Then
        assert result == "input"
        input_.assert_called_once_with("  prompt ")

    def test_input_with_failing_validator_and_cancellation(
        self, input_: MagicMock, print_: MagicMock
    ):
        # When
        result = Typer.input("prompt", validator=lambda x: x != "input")

        # Then
        assert not result
        assert input_.call_args_list == [
            call("  prompt "),
            call("  prompt "),
        ]
        assert print_.call_args_list == [
            call(""),  # Error separator
            call("  Invalid value 'input'."),
        ]

    def test_input_with_empty_value(self, monkeypatch):
        # Given
        input_ = MagicMock(side_effect=["", "input"])
        monkeypatch.setattr(Typer, "input_", input_)

        # When
        result = Typer.input("prompt")

        # Then
        assert result == "input"
        assert input_.call_args_list == [
            call("  prompt "),
            call("  prompt "),
        ]


class TestInputDate:
    @pytest.fixture(autouse=True)
    def patch_settings(patch_settings, monkeypatch: MonkeyPatch):
        monkeypatch.setattr(typer, "INDENT", 2)
        monkeypatch.setattr(typer, "WIDTH", 120)

    @pytest.mark.parametrize(
        "input_, expected",
        [
            ("18/02/2023", date_utils.date_from_str("18/02/2023")),
            ("today", date_utils.today()),
            ("yesterday", date_utils.yesterday()),
        ],
    )
    @pytest.mark.parametrize("with_separator", [True, False])
    def test_input_date(
        self,
        input_: str,
        expected: date,
        with_separator: bool,
        print_: MagicMock,
        monkeypatch: MonkeyPatch,
    ):
        # Given
        input_mock = MagicMock(return_value=input_)
        monkeypatch.setattr(Typer, "input_", input_mock)

        # Then
        assert (
            Typer.input_date("prompt", with_separator=with_separator)
            == expected
        )
        input_mock.assert_called_once_with("  prompt ")
        if with_separator:
            assert print_.call_args_list == [call("")]
        else:
            assert not print_.call_args_list

    def test_input_date_invalid_format(
        self, print_: MagicMock, monkeypatch: MonkeyPatch
    ):
        # Given
        input_mock = MagicMock(side_effect=["invalid", "18/02/2023"])
        monkeypatch.setattr(Typer, "input_", input_mock)

        # When
        date_ = Typer.input_date("prompt")

        # Then
        assert date_ == date_utils.date_from_str("18/02/2023")
        assert input_mock.call_args_list == [
            call("  prompt "),
            call("  prompt "),
        ]
        assert print_.call_args_list == [
            call(
                "  Invalid date invalid. Accepted 'today', 'yesterday', or"
                " 'dd/mm/yyyy' format."
            ),
        ]

    def test_input_date_cancel(self, monkeypatch: MonkeyPatch):
        # Given
        input_mock = MagicMock(return_value="cancel")
        monkeypatch.setattr(Typer, "input_", input_mock)

        # When
        date_ = Typer.input_date("prompt")

        # Then
        assert not date_
        input_mock.assert_called_once_with("  prompt ")


class TestSelect:
    @pytest.fixture(autouse=True)
    def patch_settings(patch_settings, monkeypatch: MonkeyPatch):
        monkeypatch.setattr(typer, "INDENT", 2)
        monkeypatch.setattr(typer, "WIDTH", 120)

    def test_select(self, print_: MagicMock, monkeypatch: MonkeyPatch):
        # Given
        input_mock = MagicMock(return_value="1")
        monkeypatch.setattr(Typer, "input_", input_mock)

        # When
        option = Typer.select(["a", "b"], prompt="Select one:")

        # When
        assert option == "a"
        input_mock.assert_called_once_with("  Enter index: ")
        assert print_.call_args_list == [
            call(""),
            call("  Select one:"),
            call(""),
            call("  1. a"),
            call("  2. b"),
        ]

    def test_select_with_display_repr(
        self, print_: MagicMock, monkeypatch: MonkeyPatch
    ):
        # Given
        input_mock = MagicMock(return_value="1")
        monkeypatch.setattr(Typer, "input_", input_mock)

        # When
        option = Typer.select(
            [1, 2], display_repr=["a", "b"], prompt="Select one:"
        )

        # When
        assert option == 1
        input_mock.assert_called_once_with("  Enter index: ")
        assert print_.call_args_list == [
            call(""),
            call("  Select one:"),
            call(""),
            call("  1. a"),
            call("  2. b"),
        ]

    @pytest.mark.parametrize("invalid_index", ["0", "3", "invalid"])
    def test_select_with_invalid_index(
        self,
        invalid_index: str,
        print_: MagicMock,
        monkeypatch: MonkeyPatch,
    ):
        # Given
        input_mock = MagicMock(side_effect=[invalid_index, "2"])
        monkeypatch.setattr(Typer, "input_", input_mock)

        # When
        option = Typer.select(["a", "b"], prompt="Select one:")

        # When
        assert option == "b"
        assert input_mock.call_args_list == [
            call("  Enter index: "),
            call("  Enter index: "),
        ]
        assert print_.call_args_list == [
            call(""),
            call("  Select one:"),
            call(""),
            call("  1. a"),
            call("  2. b"),
            call(f"  Invalid index {invalid_index!r}."),
        ]

    def test_select_without_separator(
        self, print_: MagicMock, monkeypatch: MonkeyPatch
    ):
        # Given
        input_mock = MagicMock(return_value="1")
        monkeypatch.setattr(Typer, "input_", input_mock)

        # When
        Typer.select(["a", "b"], prompt="Select one:", with_separator=False)

        # When
        assert print_.call_args_list == [
            call(""),
            call("  Select one:"),
            call("  1. a"),
            call("  2. b"),
        ]

    def test_select_with_one_line(
        self, print_: MagicMock, monkeypatch: MonkeyPatch
    ):
        # Given
        input_mock = MagicMock(return_value="1")
        monkeypatch.setattr(Typer, "input_", input_mock)

        # When
        Typer.select(["a", "b"], prompt="Select one:", one_line=True)

        # When
        assert print_.call_args_list == [
            call(""),
            call("  Select one:"),
            call(""),
            call("  1.a  2.b"),
        ]


class TestConfirm:
    @pytest.fixture(autouse=True)
    def patch_settings(patch_settings, monkeypatch: MonkeyPatch):
        monkeypatch.setattr(typer, "INDENT", 2)
        monkeypatch.setattr(typer, "WIDTH", 120)

    @pytest.mark.parametrize(
        "input_, expected", [("1", True), ("2", False)]
    )
    def test_confirm(
        self,
        input_: str,
        expected: bool,
        print_: MagicMock,
        monkeypatch: MonkeyPatch,
    ):
        # Given
        input_mock = MagicMock(return_value=input_)
        monkeypatch.setattr(Typer, "input_", input_mock)

        # When
        confirmed = Typer.confirm()

        # Then
        assert confirmed == expected
        input_mock.assert_called_once_with("  Enter index: ")
        assert print_.call_args_list == [
            call(""),
            call("  Are you sure?"),
            call("  1.Yes  2.No"),
        ]

    def test_confirm_with_invalid_index(
        self, print_: MagicMock, monkeypatch: MonkeyPatch
    ):
        # Given
        input_mock = MagicMock(side_effect=["invalid", "1"])
        monkeypatch.setattr(Typer, "input_", input_mock)

        # When
        confirmed = Typer.confirm()

        # Then
        assert confirmed
        assert input_mock.call_args_list == [
            call("  Enter index: "),
            call("  Enter index: "),
        ]
        assert print_.call_args_list == [
            call(""),
            call("  Are you sure?"),
            call("  1.Yes  2.No"),
            call("  Invalid index 'invalid'."),
        ]


def test_clear(monkeypatch: MonkeyPatch):
    # Given
    mock = MagicMock()
    monkeypatch.setattr(subprocess, "run", mock)

    # When
    Typer.clear()

    # Then
    mock.assert_called_once_with(["clear"])

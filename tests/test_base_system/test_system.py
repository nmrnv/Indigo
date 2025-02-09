import contextlib
import io
import typing as t
from unittest.mock import MagicMock

import pytest

from indigo.base import Model
from indigo.systems.models import Argument, Ask
from indigo.systems.system import System, SystemError_
from tests.conftest import DatabaseRecordStub


class TestDatabase:
    @pytest.fixture
    def patch_database(patch_database):
        pass

    def test(self):
        # Then
        assert (
            System.make_database().name
            == System().database.name
            == "System"
        )


def test_name(system: System):
    # Then
    assert system.name == system.__class__.__name__


def test_init(system: System):
    # Then
    assert system.database


def test_start(system: System, typer_mock):
    # Given
    system._on_start = MagicMock()
    system._handle_ask = MagicMock(side_effect=lambda _: system._exit())  # type: ignore
    typer_mock.input = lambda **_: "exit"

    # When
    system.start()

    # Then
    system._on_start.assert_called_once()
    system._handle_ask.assert_called_once_with("exit")


def test_start_with_init_command(system: System):
    # Given
    system._handle_ask = MagicMock(side_effect=lambda _: system._exit())  # type: ignore
    stream = io.StringIO()

    # When
    with (
        contextlib.redirect_stdout(stream),
        contextlib.redirect_stderr(stream),
    ):
        system.start(init_command="exit")

    # Then
    system._handle_ask.assert_called_once_with("exit")


def test_gather_asks():
    # Given
    class TestSystem(System):
        @System.ask("command")
        def method(self): ...

        @System.ask("command two")
        def method_two(self, _: str): ...

        @System.ask("command three")
        def method_three(self, _: DatabaseRecordStub): ...

    class TestSystemTwo(System):
        @System.ask("command")
        def method(self, _: int): ...

        @System.ask("command two")
        def method_two(self, _: t.Optional[str] = None): ...

        @System.ask("command three")
        def method_three(
            self, _: t.Optional[DatabaseRecordStub] = None
        ): ...

    # Then
    assert System.asks[TestSystem.__name__]["command"] == Ask(
        "command", "method", []
    )
    assert System.asks[TestSystem.__name__]["command two"] == Ask(
        "command two", "method_two", [Argument("_", str, False)]
    )
    assert System.asks[TestSystem.__name__]["command three"] == Ask(
        "command three",
        "method_three",
        [Argument("_", DatabaseRecordStub, False)],
    )

    assert System.asks[TestSystemTwo.__name__]["command"] == Ask(
        "command", "method", [Argument("_", int, False)]
    )
    assert System.asks[TestSystemTwo.__name__]["command two"] == Ask(
        "command two", "method_two", [Argument("_", str, True)]
    )
    assert System.asks[TestSystemTwo.__name__]["command three"] == Ask(
        "command three",
        "method_three",
        [Argument("_", DatabaseRecordStub, True)],
    )


@pytest.mark.parametrize(
    "ask",
    [
        "three worded ask",
        "underscore_ask space start",
        "space end ",
        "symbol @",
        "number 1@",
        "1",
    ],
)
def test_gather_asks_definition_failures(ask: str):
    # Then
    with pytest.raises(
        SystemError_, match="can only contain lowercase letters"
    ):
        # When
        class _(System):
            @System.ask(ask)
            def method(self): ...


def test_gather_asks_failure_with_non_self_first_parameter():
    # Then
    with pytest.raises(
        SystemError_, match="must have 'self' as first parameter"
    ):
        # When
        class _(System):
            @System.ask("ask")
            def method(non_self): ...


def test_gather_asks_failure_with_no_type_annotations():
    # Then
    with pytest.raises(
        SystemError_, match="parameters must be type-annotated"
    ):
        # When
        class _(System):
            @System.ask("ask")
            def method(self, _): ...


@pytest.mark.parametrize(
    "type_, argument, expected_value",
    [
        (int, "1", 1),
        (float, "1.1", 1.1),
        (str, "a", "a"),
    ],
)
def test_type_annotations_and_cast(type_, argument, expected_value):
    # Given
    class TestSystem(System):
        @System.ask("method")
        def _method(self, parameter: type_):
            self.argument = parameter

    system = TestSystem()

    # When
    system._handle_ask(f"method {argument}")

    # Then
    assert system.argument == expected_value
    del System.asks["TestSystem"]  # type: ignore


@pytest.mark.parametrize(
    "type_", [t.Sequence, Model, bool, bytes, dict, list, set]
)
def test_not_allowed_type_annotation_types(type_):
    # Then
    with pytest.raises(
        SystemError_,
        match=(
            "parameters can only be str, int or float, including optional"
        ),
    ):
        # When
        class _(System):
            @System.ask("ask")
            def method(self, _: type_): ...


def test_not_allowed_optional_argument_without_a_default_none_value():
    # Then
    with pytest.raises(
        SystemError_,
        match="optional arguments must have None as a default value",
    ):
        # When
        class _(System):
            @System.ask("ask")
            def method(self, _: t.Optional[str]): ...

    # Then
    with pytest.raises(
        SystemError_,
        match="optional arguments must have None as a default value",
    ):
        # When
        class _(System):
            @System.ask("ask")
            def method(
                self, _: t.Optional[str], __: t.Optional[str] = None
            ): ...


def test_not_allowed_required_argument_with_default_value():
    # Then
    with pytest.raises(
        SystemError_,
        match="Required arguments cannot have default values",
    ):
        # When
        class _(System):
            @System.ask("ask")
            def method(self, _: str = "default"): ...


def test_gather_asks_failure_with_varargs():
    # Then
    with pytest.raises(SystemError_, match="cannot contain varargs"):
        # When
        class _(System):
            @System.ask("ask")
            def method(self, *_): ...


def test_gather_asks_failure_with_kwargs():
    # Then
    with pytest.raises(SystemError_, match="cannot contain kwargs"):
        # When
        class _(System):
            @System.ask("ask")
            def method(self, *, _): ...


def test_gather_asks_failure_with_return_annotation():
    # Then
    with pytest.raises(SystemError_, match="cannot have return"):
        # When
        class _(System):
            @System.ask("ask")
            def method(self) -> str: ...


def test_gather_asks_failure_base_override():
    # Then
    with pytest.raises(
        SystemError_, match="cannot override the system ask"
    ):
        # When
        class _(System):
            def _on_start(self):
                pass

            @System.ask("help")
            def method(self): ...


def test_gather_asks_failure_duplicate_override():
    # Then
    with pytest.raises(SystemError_, match="is already defined"):
        # When
        class _(System):
            @System.ask("command")
            def method(self):  # type: ignore
                ...

            @System.ask("command")
            def method(self): ...


def test_handle_ask(system: System):
    # Given
    system.test_ask = MagicMock()  # type: ignore

    # When
    system._handle_ask("ask argument")

    # Then
    system.test_ask.assert_called_once_with("argument")  # type: ignore


def test_handle_optional_ask(system: System):
    # Given
    system.test_optional_ask = MagicMock()  # type: ignore

    # When
    system._handle_ask("optional ask argument")

    # Then
    system.test_optional_ask.assert_called_once_with(  # type: ignore
        "argument", None
    )

    # Given
    system.test_optional_ask.reset_mock()  # type: ignore

    # When
    system._handle_ask("optional ask argument second_argument")

    # Then
    system.test_optional_ask.assert_called_once_with(  # type: ignore
        "argument", "second_argument"
    )


def test_handle_ask_prefers_two_worded_ask():
    # Given
    mock = MagicMock()

    class TestSystem(System):
        def _on_start(self):
            pass

        @System.ask("start")
        def _start(self):
            mock(self._start)

        @System.ask("start custom")
        def _start_custom(self):
            mock(self._start_custom)

    system = TestSystem()

    # When
    system._handle_ask("start custom")

    # Then
    mock.assert_called_once_with(system._start_custom)


def test_handle_ask_from_base_system(system: System):
    # Given
    system._help = MagicMock()

    # When
    system._handle_ask("help")

    # Then
    system._help.assert_called_once()


def test_handle_ask_end_to_end(system: System):
    # Given
    system._on = True
    stream = io.StringIO()

    # When
    with (
        contextlib.redirect_stdout(stream),
        contextlib.redirect_stderr(stream),
    ):
        system._handle_ask("exit")

    # Then
    assert not system._on


def test_handle_ask_failure_when_ask_not_found(system: System, typer_mock):
    # When
    system._handle_ask("invalid ask")

    # Then
    typer_mock.header.assert_called_once_with(
        "Ask 'invalid ask' not found."
    )


def test_handle_ask_failure_with_extra_arguments(
    system: System, typer_mock
):
    # When
    system._handle_ask("help invalid_arg")

    # Then
    typer_mock.header.assert_called_once_with(
        "Invalid number of arguments. None required."
    )


def test_handle_ask_failure_with_argument_mismatch_less(
    system: System, typer_mock
):
    # When
    system._handle_ask("optional ask")

    # Then
    typer_mock.header.assert_called_once_with(
        "Invalid number of arguments. Required: argument,"
        " optional_argument?."
    )


def test_handle_ask_failure_with_argument_mismatch_more(
    system: System, typer_mock
):
    # When
    system._handle_ask("ask arg1 arg2")  # requires 1 argument

    # Then
    typer_mock.header.assert_called_once_with(
        "Invalid number of arguments. Required: argument."
    )


def test_handle_ask_failure_with_system_exception():
    # Given
    class TestSystem(System):
        @System.ask("ask")
        def _ask(self):
            raise SystemError_("Exception")

    system = TestSystem()

    # Then
    with pytest.raises(SystemError_) as e:
        # When
        system._handle_ask("ask")

    assert str(e.value) == "Exception"
    del System.asks["TestSystem"]  # type: ignore

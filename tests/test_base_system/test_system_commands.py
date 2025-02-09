from unittest.mock import MagicMock, call

from indigo.systems.system import System as System
from indigo.tools.linker import Linker


def test_current_system(system: System, typer_mock):
    # When
    system._handle_ask("cs")

    # Then
    typer_mock.header.assert_called_with("TestSystem")


def test_help(system: System, typer_mock):
    # When
    system._handle_ask("help")

    # Then
    assert typer_mock.list.call_count == 2
    args_list = typer_mock.list.call_args_list
    assert args_list[0] == call(["ask", "optional ask"], enumerated=False)
    assert args_list[1] == call(
        [
            "cs",
            "help",
            "archive",
            "exit",
            "farewell",
        ],
        enumerated=False,
    )


def test_help_on_base_system(typer_mock):
    # Given
    base_system = System()

    # When
    base_system._handle_ask("help")

    # Then
    typer_mock.list.assert_called_once_with(
        [
            "cs",
            "help",
            "archive",
            "exit",
            "farewell",
        ],
        enumerated=False,
    )


def test_help_failure_with_no_asks(typer_mock):
    # Given
    class _TestSystem(System): ...

    system = _TestSystem()

    # When
    system._handle_ask("help")

    # Then
    typer_mock.body.assert_called_once_with("_TestSystem has no asks.")


def test_exit(system: System, monkeypatch):
    # Given
    system._on = True
    unlink = MagicMock()
    monkeypatch.setattr(Linker, "unlink", unlink)

    # When
    system._handle_ask("exit")

    # Then
    assert not system._on
    unlink.assert_called_once()


def test_farewell(system: System, monkeypatch):
    # Given
    import sys

    exit_mock = MagicMock()
    monkeypatch.setattr(sys, "exit", exit_mock)

    # When
    system._handle_ask("farewell")

    # Then
    exit_mock.assert_called_once_with(0)

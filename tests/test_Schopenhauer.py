import typing as t
from argparse import Namespace
from unittest.mock import MagicMock

import pytest

from indigo import Indigo, make_parser, start_system


def test_start_system(monkeypatch):
    # Given
    indigo = MagicMock()
    monkeypatch.setattr("indigo.Indigo", lambda: indigo)

    config = MagicMock()
    monkeypatch.setattr("indigo.Config", config)
    namespace = Namespace(**{"debug": False, "system": None})

    # When
    start_system(namespace=namespace)

    # Then
    config.make.assert_called_once_with(debug=False)
    indigo.start.assert_called_once()


@pytest.mark.parametrize(
    "arguments, expected_debug, expected_init_system",
    [
        ([], True, None),
        (["-d", "true", "-s", "as"], True, "as"),
        (["-d", "True", "-s", "ws"], True, "ws"),
        (["-d", "false", "-s", "hs"], False, "hs"),
        (["-d", "False", "-s", "ps"], False, "ps"),
        (["-d", "False", "-s", "ss"], False, "ss"),
        (["-d", "True"], True, None),
        (["-d", "False"], False, None),
    ],
)
def test_parser(
    arguments: t.Sequence[str],
    expected_debug: bool,
    expected_init_system: t.Optional[str],
):
    # Given
    parser = make_parser()

    # When
    namespace = parser.parse_args(arguments)

    # Then
    assert namespace.debug == expected_debug
    assert namespace.system == expected_init_system


@pytest.mark.parametrize(
    "arguments",
    [
        ["-d", "invalid_value"],
        ["-s", "invalid_value"],
        ["-a", "invalid_argument"],
        ["-h"],
    ],
)
def test_parser_failure(arguments: t.Sequence[str]):
    # Given
    parser = make_parser()

    # Then
    with pytest.raises(SystemExit):
        # When
        parser.parse_args(arguments)


@pytest.fixture
def indigo():
    return Indigo()


@pytest.mark.parametrize("system, command", [("PurposeSystem", "ps")])
def test_start_systems(
    indigo: Indigo, system: str, command: str, monkeypatch
):
    # Given
    will_system = MagicMock()
    monkeypatch.setattr(f"indigo.{system}", lambda: will_system)

    # When
    indigo._handle_ask(command)

    # Then
    will_system.start.assert_called_once()

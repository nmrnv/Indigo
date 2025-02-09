import pytest

from indigo.base import ID
from indigo.tools.linker import Linker, LinkerError


@pytest.fixture(autouse=True)
def linker():
    yield
    Linker.unlink()


def test_linker():
    # Given
    id_1, id_2 = ID(), ID()
    ids = [id_1, id_2]
    assert not Linker.is_linked()
    assert Linker.links() == []

    # When
    Linker.link(str, ids, extra={"key": "value"})

    # Then
    assert Linker.is_linked()
    assert Linker.links() == ids

    # When
    resolved_id = Linker.resolve(str, "1")
    resolved_cast_id = Linker.resolve(str, 2)

    # Then
    assert resolved_id == id_1
    assert resolved_cast_id == id_2


def test_resolve_with_no_linked_ids():
    # Then
    with pytest.raises(LinkerError, match="No linked ids."):
        # When
        Linker.resolve(str, 0)


def test_resolve_with_different_cls():
    # Given
    ids = [ID()]
    Linker.link(str, ids)

    # Then
    with pytest.raises(LinkerError):
        # When
        Linker.resolve(int, 0)


@pytest.mark.parametrize("non_integer_index", ["invalid_int", "2.0", "2.3"])
def test_resolve_with_non_integers(non_integer_index):
    # Given
    ids = [ID()]
    Linker.link(str, ids)

    # Then
    with pytest.raises(LinkerError):
        # When
        Linker.resolve(str, non_integer_index)


@pytest.mark.parametrize("invalid_index", [0, 2, -1])
def test_resolve_with_invalid_index(invalid_index):
    # Given
    ids = [ID()]
    Linker.link(str, ids)

    # Then
    with pytest.raises(LinkerError):
        # When
        Linker.resolve(str, invalid_index)

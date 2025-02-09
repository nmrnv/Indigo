import typing as t

from indigo.base import ID, Error


class LinkerError(Error): ...


class Linker:
    Link = t.Tuple[t.Type, t.Sequence[ID]]
    _link: t.ClassVar[t.Optional[Link]] = None
    extra: t.ClassVar[t.Mapping] = {}

    @classmethod
    def links(cls) -> t.Sequence[ID]:
        if not cls._link:
            return []
        return cls._link[1]

    @classmethod
    def is_linked(cls) -> bool:
        return cls._link is not None

    @classmethod
    def link(
        cls,
        type_: t.Type,
        ids: t.Sequence[ID],
        extra: t.Optional[t.Mapping] = None,
    ):
        cls._link = (type_, ids)
        cls.extra = extra or {}

    @classmethod
    def unlink(cls):
        cls._link = None
        cls.extra = {}

    @classmethod
    def resolve(cls, type_: t.Type, index: t.Union[int, str]) -> ID:
        try:
            index = int(index)
        except ValueError:
            raise LinkerError("Index must be an integer.")

        if not cls._link:
            raise LinkerError("No linked ids. List objects to link.")

        linked_type, ids = cls._link

        if type_ is not linked_type:
            raise LinkerError(
                f"Cannot resolve {type_.__name__} "
                f"from linked cls {linked_type.__name__}."
            )

        if index < 1 or index > len(ids):
            # Indexing is from 1 because of the way it is selected
            # through the CLI, where items are enumerated starting from 1.
            raise LinkerError(
                f"Invalid index {index}. Indices are from 1 to {len(ids)}"
            )

        return ids[index - 1]

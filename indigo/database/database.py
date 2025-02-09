import typing as t
from importlib import import_module

from indigo.database.models import (
    DatabaseError,
    DatabaseRecord,
    DatabaseRecord_,
    MetadataRecord,
    MetadataRecord_,
)
from indigo.database.mongodb import CODEC_OPTIONS, Collection, make_client


@t.final
class Database:
    name: str

    def __init__(self, name: str):
        self.name = name
        self.database = make_client().get_database(name)
        self.metadata = self.database.get_collection(
            name="metadata", codec_options=CODEC_OPTIONS
        )

    def _collection(self, cls: t.Type[DatabaseRecord_]) -> Collection:
        name = cls.__name__
        return self.database.get_collection(
            name=name, codec_options=CODEC_OPTIONS
        )

    class Decorators:
        @staticmethod
        def validate_entity(exists: bool):
            def wrapper(method: t.Callable):
                def validate(self: "Database", entity: t.Any):
                    if not isinstance(entity, DatabaseRecord):
                        raise DatabaseError(
                            f"Entity {entity!r} must be a DatabaseRecord."
                        )
                    cls = entity.__class__
                    collection = self._collection(cls)
                    in_database = (
                        collection.count_documents({"_id": entity.id_}) > 0
                    )
                    if exists and not in_database:
                        raise DatabaseError(
                            f"There is no record of type {cls!r} with id"
                            f" {entity.id_!r}."
                        )
                    elif not exists and in_database:
                        raise DatabaseError(
                            f"Entity with id {entity.id_!r} already exists."
                            " Update instead."
                        )
                    return method(self, entity, collection)

                return validate

            return wrapper

    # Entity Operations
    def count(self, cls: t.Type[DatabaseRecord_]) -> int:
        return self._collection(cls).count_documents({})

    def exists(self, cls: t.Type[DatabaseRecord_], id_: str) -> bool:
        return self._collection(cls).find_one({"_id": id_}) is not None

    @Decorators.validate_entity(exists=False)
    def save(self, entity: DatabaseRecord, collection: Collection):
        collection.insert_one(entity.model_dump(by_alias=True))

    @Decorators.validate_entity(exists=True)
    def update(self, entity: DatabaseRecord, collection: Collection):
        collection.update_one(
            {"_id": entity.id_}, {"$set": entity.model_dump(by_alias=True)}
        )

    def retrieve(
        self, cls: t.Type[DatabaseRecord_], id_: str
    ) -> t.Optional[DatabaseRecord_]:
        record = self._collection(cls).find_one({"_id": id_})
        if not record:
            return None
        return cls(**record)

    def list(
        self,
        cls: t.Type[DatabaseRecord_],
        predicate: t.Optional[t.Callable[[DatabaseRecord_], bool]] = None,
    ) -> t.List[DatabaseRecord_]:
        # Optimisation needed! The predicate needs to
        # work with MongoDB's filtering, and not as a consequence
        records = list(self._collection(cls).find())
        items = [cls(**record) for record in records]
        return (
            items if not predicate else [i for i in items if predicate(i)]
        )

    def delete(self, cls: t.Type[DatabaseRecord_], id_: str):
        if not self.exists(cls, id_):
            raise DatabaseError(
                f"There is no record of type {cls!r} with id {id_!r}."
            )
        self._collection(cls).delete_one({"_id": id_})

    def save_update_delete(
        self,
        cls: t.Type[DatabaseRecord_],
        items: t.Sequence[DatabaseRecord_],
    ) -> t.Tuple[
        t.Sequence[DatabaseRecord_],
        t.Sequence[DatabaseRecord_],
        t.Sequence[DatabaseRecord_],
        t.Sequence[DatabaseRecord_],
    ]:
        # WARNING!!! This deletes all entities besides the ones provided
        existing_items_by_id = {item.id_: item for item in self.list(cls)}
        saved: t.List[DatabaseRecord_] = []
        updated: t.List[DatabaseRecord_] = []
        deleted: t.List[DatabaseRecord_] = []
        unchanged: t.List[DatabaseRecord_] = []

        for item in items:
            item_type = item.__class__
            if existing_item := self.retrieve(item_type, item.id_):
                del existing_items_by_id[item.id_]
                if item == existing_item:
                    unchanged.append(item)
                else:
                    self.update(item)
                    updated.append(item)
            else:
                self.save(item)
                saved.append(item)
        for id_, item in existing_items_by_id.items():
            self.delete(item.__class__, id_)
            deleted.append(item)

        return saved, updated, deleted, unchanged

    # Metadata Operations

    def meta_exists(self, cls: t.Type[MetadataRecord_]) -> bool:
        return self.metadata.count_documents({"_id": cls.key}) > 0

    def meta_set(self, record: MetadataRecord):
        if not isinstance(record, MetadataRecord):
            raise DatabaseError(
                "Only subclasses of MetadataRecord can be saved as"
                " metadata."
            )
        if self.meta_exists(record.__class__):
            self.metadata.find_one_and_update(
                {"_id": record.id_},
                {"$set": record.dict()},
            )
        else:
            self.metadata.insert_one(record.dict())

    def meta_retrieve(
        self, cls: t.Type[MetadataRecord_]
    ) -> t.Optional[MetadataRecord_]:
        if not (record := self.metadata.find_one({"_id": cls.key})):
            return None
        type_ = record.pop("type")
        module_path, class_name = type_.strip(" ").rsplit(".", 1)
        class_ = getattr(import_module(module_path), class_name)
        return class_(**record)

    def meta_delete(self, cls: t.Type[MetadataRecord_]):
        if not self.meta_exists(cls):
            raise DatabaseError(
                f"There is no meta value set for {cls.__name__!r}."
            )
        self.metadata.delete_one({"_id": cls.key})

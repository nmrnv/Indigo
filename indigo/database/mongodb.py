from bson import CodecOptions
from pymongo import MongoClient
from pymongo.collection import Collection

from indigo.config import Config
from indigo.utils.date_utils import TIMEZONE_UTC

__all__ = ["make_client", "Collection", "CODEC_OPTIONS"]

client = None


def make_client() -> MongoClient:
    global client
    if client:
        return client
    username = Config.database_config.username
    password = Config.database_config.password
    port = "27017" if not Config.debug else "27018"
    client = MongoClient(
        f"mongodb://{username}:{password}@127.0.0.1:{port}",
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
    )
    return client


CODEC_OPTIONS = CodecOptions(tz_aware=True, tzinfo=TIMEZONE_UTC)

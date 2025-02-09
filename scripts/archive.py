import shutil
import sys
import typing as t
from pathlib import Path

from archive_download import validate_last_archive
from archive_models import ArchiveMetadata
from bson import json_util
from cryptography.fernet import Fernet

sys.path.append(Path().parent.as_posix())

from indigo.aws.client import AWSClient
from indigo.config import Config
from indigo.database.mongodb import make_client
from indigo.utils import date_utils, path_utils
from start import make_parser


def make_paths() -> t.Tuple[Path, Path, Path]:
    root_directory = Config.router.root_directory
    archive_directory = (
        root_directory.parent / f"{root_directory.name}.archive"
    )
    archive_zip_path = (
        archive_directory.parent / f"{archive_directory.name}.zip"
    )
    encrypted_zip_path = (
        archive_directory.parent / f"{archive_directory.name}.zip.encrypted"
    )
    return archive_directory, archive_zip_path, encrypted_zip_path


def dump_database(directory: Path):
    client = make_client()
    for database_name in client.list_database_names():
        if database_name in ("admin", "config", "local"):
            continue
        database = client.get_database(database_name)
        database_directory = directory / database_name
        database_directory.mkdir()
        for collection_name in database.list_collection_names():
            collection = database.get_collection(collection_name)
            collection_filepath = (
                database_directory / f"{collection_name}.json"
            )
            items_json = json_util.dumps(collection.find(), indent=4)
            with open(collection_filepath, "w") as collection_file:
                collection_file.write(items_json)


def archive():
    print("Archiving current data…")
    archive_directory, archive_zip_path, encrypted_zip_path = make_paths()

    # Create the temporary archive directory
    if archive_directory.exists():
        path_utils.delete_directory(archive_directory)
    else:
        archive_directory.mkdir(parents=True)

    print("Building archive…")
    # Move all necessary files
    # Copy the mongodb data
    path_utils.copy_directory(
        from_=Config.database_config.directory,
        to=archive_directory / "mongodb",
    )
    path_utils.delete_directory(archive_directory / "mongodb" / "journal")
    path_utils.delete_directory(
        archive_directory / "mongodb" / "diagnostic.data"
    )

    # Generate the readable mongodb data
    mongo_db_readable_directory = archive_directory / "mongodb_readable"
    mongo_db_readable_directory.mkdir()
    dump_database(mongo_db_readable_directory)

    # Copy the notes
    path_utils.copy_directory(
        from_=Config.router.notes_directory, to=archive_directory / "notes"
    )

    # Generate and save archive metadata
    print("Generating metadata…")
    metadata = ArchiveMetadata.generate(archive_directory)
    archive_metadata_path = archive_directory / "metadata.json"
    archive_metadata_path.write_text(metadata.json(indent=4))

    # Zip the archive
    print("Zipping archive…")
    shutil.make_archive(
        base_name=archive_directory.as_posix(),
        format="zip",
        root_dir=Config.router.root_directory.parent,
        base_dir=archive_directory.name,
    )

    # Encrypt the archive
    print("Encrypting archive…")
    fernet = Fernet(Config.encryption_key)
    with open(archive_zip_path, "rb") as zipped_archive:
        zipped_file_contents = zipped_archive.read()
    with open(encrypted_zip_path, "wb") as encrypted_archive:
        encrypted_contents = fernet.encrypt(zipped_file_contents)
        encrypted_archive.write(encrypted_contents)

    # Send the archive
    print("Uploading archive…")
    aws_client = AWSClient()
    aws_client.upload_file(encrypted_zip_path)

    print("Data archived successfully.")


def cleanup():
    archive_directory, archive_zip_path, encrypted_zip_path = make_paths()
    path_utils.delete_directory(archive_directory)
    if archive_zip_path.exists():
        path_utils.delete_file(archive_zip_path)
    if encrypted_zip_path.exists():
        path_utils.delete_file(encrypted_zip_path)


if __name__ == "__main__":
    print("Archiving data…")
    namespace = make_parser().parse_args()
    Config.make(debug=namespace.debug)

    error = None
    try:
        validate_last_archive()
        archive()
    except Exception as e:
        error = e
        print(f"Data archive failed. Error: {e}.")

    logs = []
    log_path = Config.router.root_directory / "archive.log"
    if log_path.exists():
        with open(log_path, "r") as file:
            logs = file.readlines()
    with open(log_path, "w") as file:
        error_message = str(error).replace("\n", "") if error else None
        log = (
            "Archive successful"
            if not error
            else f"Archive failed with error: {error_message}"
        )
        timed_log = f"{date_utils.datetime_str(date_utils.now())}: {log}\n"
        lines_to_write = logs if len(logs) < 10 else logs[-10:]
        file.writelines([*lines_to_write, timed_log])

    cleanup()

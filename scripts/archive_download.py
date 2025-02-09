import shutil
import sys
import typing as t
from pathlib import Path

from archive_models import ArchiveMetadata
from cryptography.fernet import Fernet

sys.path.append(Path().parent.as_posix())

from indigo.aws.client import AWSClient
from indigo.config import Config
from indigo.models.base import Error
from indigo.utils import path_utils
from start import make_parser


class ArchiveValidationError(Error): ...


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


def download_archive():
    print("Downloading archive…")
    _, archive_zip_path, encrypted_zip_path = make_paths()

    # Download the encrypted archive
    aws_client = AWSClient()
    if not aws_client.exists(encrypted_zip_path.name):
        print("No previous archive exists.")
        return
    aws_client.download_file(encrypted_zip_path.name, encrypted_zip_path)

    # Decrypt it
    print("Decrypting archive…")
    fernet = Fernet(Config.encryption_key)
    with open(encrypted_zip_path, "rb") as file:
        encrypted_file = fernet.decrypt(file.read())
    with open(archive_zip_path, "wb") as file:
        file.write(encrypted_file)

    # Unzip it
    print("Unzipping archive…")
    shutil.unpack_archive(
        filename=archive_zip_path, extract_dir=archive_zip_path.parent
    )

    cleanup(delete_archive=False)
    print("Download and decrypt completed successfully.")


def validate_last_archive():
    print("Validating previous archive…")
    archive_directory, _, encrypted_zip_path = make_paths()

    aws_client = AWSClient()
    if not aws_client.exists(encrypted_zip_path.name):
        print("No previous archive exists.")
        return

    download_archive()

    received_metadata_path = archive_directory / "metadata.json"
    received_metadata = ArchiveMetadata.parse_file(received_metadata_path)
    expected_metadata = ArchiveMetadata.generate(archive_directory)

    exclude = {"commit_hash", "datetime_str"}
    if received_metadata.model_dump(
        exclude=exclude
    ) != expected_metadata.dict(exclude=exclude):
        raise ArchiveValidationError("Archive validation error")

    cleanup(delete_archive=True)
    print("Previous archive validated successfully.")


def cleanup(delete_archive: bool):
    archive_directory, archive_zip_path, encrypted_zip_path = make_paths()
    if delete_archive:
        path_utils.delete_directory(archive_directory)
    if archive_zip_path.exists():
        path_utils.delete_file(archive_zip_path)
    if encrypted_zip_path.exists():
        path_utils.delete_file(encrypted_zip_path)


if __name__ == "__main__":
    namespace = make_parser().parse_args()
    Config.make(debug=namespace.debug)
    download_archive()

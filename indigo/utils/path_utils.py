import os
import subprocess
import typing as t
from pathlib import Path

from indigo.models.base import Error

Size = int
DirectoryName = FileName = str
DirectoryStructure = t.Dict[
    str, t.Union[t.List[FileName], "DirectoryStructure"]
]


class PathUtilsError(Error): ...


def get_directory_size(directory: Path) -> Size:
    size = 0
    for path, _, files in os.walk(directory.as_posix()):
        for file in files:
            filepath = Path(path) / file
            size += filepath.stat().st_size
    return size


def get_directory_structure(directory: Path) -> DirectoryStructure:
    structure: DirectoryStructure = {"files": []}
    for item in os.scandir(directory.as_posix()):
        item = Path(item)
        if item.is_file():
            structure["files"].append(item.name)
        elif item.is_dir():
            structure[item.name] = get_directory_structure(directory / item)  # type: ignore
    structure = dict(sorted(structure.items(), key=lambda pair: pair[0]))
    structure["files"].sort()
    return structure


def copy_directory(from_: Path, to: Path):
    try:
        subprocess.run(
            f"cp -rp -f {from_.as_posix()} {to.as_posix()}",
            shell=True,
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode("utf-8").strip()
        raise PathUtilsError(
            f"Copying directory failed with error: {error_message}"
        )


def delete_directory(directory: Path):
    try:
        subprocess.run(
            f"rm -rf {directory.as_posix()}",
            shell=True,
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode("utf-8").strip()
        raise PathUtilsError(
            f"Deleting directory failed with error: {error_message}"
        )


def copy_file(from_: Path, to: Path):
    try:
        subprocess.run(
            f"cp -f {from_.as_posix()} {to.as_posix()}",
            shell=True,
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode("utf-8").strip()
        raise PathUtilsError(
            f"Copying file failed with error: {error_message}"
        )


def delete_file(filepath: Path):
    if filepath.exists():
        os.remove(filepath.as_posix())
    else:
        raise PathUtilsError(f"File at {filepath!r} does not exist.")

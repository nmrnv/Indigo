import sys
import typing as t
from pathlib import Path

import docker
from docker.models.containers import Container

sys.path.append(Path().parent.as_posix())

from indigo.config import Config
from start import make_parser


def stop_database():
    is_dev = "development " if Config.debug else ""
    print(f"Stopping Indigo {is_dev}database…")
    client = docker.from_env()
    container_name = (
        "indigo.database" if not Config.debug else "indigo.database.debug"
    )
    existing_containers = [
        t.cast(Container, container)
        for container in client.containers.list(
            all=True, filters={"name": rf"^{container_name}$"}
        )
    ]
    try:
        container = existing_containers[0]
        if container.status == "exited":
            print("Container is already inactive.")
        else:
            container.stop()
            print("Container stopped successfully.")
    except IndexError:
        print("Container does not exist.")

    client.close()


if __name__ == "__main__":
    namespace = make_parser().parse_args()
    Config.make(debug=namespace.debug)
    stop_database()

import os
import sys
import typing as t
from pathlib import Path

import docker
from docker.models.containers import Container
from docker.models.images import Image

sys.path.append(Path().parent.as_posix())

from indigo.config import Config
from start import make_parser


def start_database():
    is_dev = "development " if Config.debug else ""
    print(f"Starting Indigo {is_dev}database…")
    client = docker.from_env()
    container_name = (
        "indigo.database" if not Config.debug else "indigo.database.debug"
    )
    existing_containers: t.Sequence[Container] = [
        t.cast(Container, container)
        for container in client.containers.list(
            all=True, filters={"name": rf"^{container_name}$"}
        )
    ]
    try:
        container = existing_containers[0]
        if not container.status == "running":
            container.start()
            print("Container started successfully.")
        else:
            print("Container is already running.")
    except IndexError:
        image_name = "indigo_db"
        if not any(
            [
                image
                for image in t.cast(t.Sequence[Image], client.images.list())
                if "indigo_db:latest" in image.tags
            ]
        ):
            client.images.build(
                tag=image_name,
                path=Path(__file__).parent.parent.as_posix(),
                buildargs={
                    "USER_ID": str(
                        uid if (uid := os.getuid()) > 999 else 999
                    ),
                    "GROUP_ID": str(
                        gid if (gid := os.getgid()) > 999 else 999
                    ),
                },
            )
        client.containers.run(
            image=image_name,
            name=container_name,
            detach=True,
            ports={"27017": 27017 if not Config.debug else 27018},
            volumes=[
                f"{Config.database_config.directory.as_posix()}:/data/db/"
            ],
            environment={
                "MONGO_INITDB_ROOT_USERNAME": (
                    Config.database_config.username
                ),
                "MONGO_INITDB_ROOT_PASSWORD": (
                    Config.database_config.password
                ),
            },
        )
        print("Container started successfully.")
    client.close()


if __name__ == "__main__":
    namespace = make_parser().parse_args()
    Config.make(debug=namespace.debug)
    start_database()

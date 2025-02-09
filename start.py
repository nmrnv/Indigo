from argparse import ArgumentParser, ArgumentTypeError, Namespace

from indigo.config import Config
from indigo.systems.purpose.purpose_system import PurposeSystem
from indigo.systems.system import System
from indigo.tools.typer import Typer


class Indigo(System):
    def _on_start(self):
        Typer.header(f"Debug: {Config.debug}")

    @System.ask("ps")
    def _start_purpose_system(self):
        PurposeSystem().start()


def make_parser() -> ArgumentParser:
    def is_debug(argument):
        if argument.lower() == "false":
            return False
        elif argument.lower() == "true":
            return True
        raise ArgumentTypeError("True or false expected.")

    def validate_init_system(argument):
        if argument not in ("as", "ws", "hs", "ps", "ss"):
            raise ArgumentTypeError(
                f"Invalid init system identifier {argument}."
            )
        return argument

    parser = ArgumentParser()
    parser.add_argument("-debug", dest="debug", type=is_debug, default=True)
    parser.add_argument(
        "-system", dest="system", type=validate_init_system, default=None
    )
    return parser


def start_system(namespace: Namespace):
    Config.make(debug=namespace.debug)
    Indigo().start(init_command=namespace.system)
    Typer.separator()


if __name__ == "__main__":
    Typer.clear()
    arguments_parser = make_parser()
    start_system(namespace=arguments_parser.parse_args())

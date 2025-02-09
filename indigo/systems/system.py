import functools
import inspect
import re
import readline
import sys
import typing as t
from abc import ABC, abstractmethod

from indigo.base import ID, Error
from indigo.config import Config
from indigo.database.database import Database
from indigo.database.models import DatabaseRecord
from indigo.systems.models import Argument, Ask, AskDefinition
from indigo.tools.linker import Linker, LinkerError
from indigo.tools.typer import Typer

SystemName = str
BASE_SYSTEM = "System"
readline.clear_history()


class SystemError_(Error): ...


class SystemABC(ABC):
    database: Database

    asks: t.ClassVar[t.Dict[SystemName, t.Dict[AskDefinition, Ask]]] = {}

    @classmethod
    def make_database(cls) -> Database:
        return Database(name=cls.__name__)

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def _on_start(self):
        raise NotImplementedError

    def __init__(self):
        self._on = False
        self.database = self.__class__.make_database()

    @t.final
    def start(self, init_command: t.Optional[str] = None):
        self._on = True
        self._on_start()

        if init_command:
            Typer.clear()
            self._handle_ask(init_command)

        while self._on:
            prompt = ">" if not Config.debug else "debug >"
            if ask := Typer.input(
                prompt=prompt, cancellable=False, with_separator=True
            ):
                Typer.clear()
                self._handle_ask(ask)

    @t.final
    def exit(self):
        Typer.header(f"{self.name} exited.")
        Linker.unlink()
        self._on = False

    @classmethod
    @t.final
    def ask(cls, definition: AskDefinition):
        def gather(method: t.Callable):
            system, method_name = method.__qualname__.split(".")[-2:]
            location = f"{system}:{method_name}:{definition}:"

            if system not in cls.asks:
                cls.asks[system] = {}
            if definition in cls.asks[BASE_SYSTEM]:
                raise SystemError_(
                    f"{location} You cannot override the system ask:"
                    f" {definition!r}."
                )
            if definition in cls.asks[system]:
                raise SystemError_(
                    f"{location} Ask is already defined for method"
                    f" {cls.asks[system][definition].method_name!r}"
                )

            if not re.match(r"^[a-z]+[\s{1}]?[a-z]+?$", definition):
                raise SystemError_(
                    f"{location} Ask can only contain lowercase letters"
                    " and be up to two words."
                )

            arg_spec = inspect.getfullargspec(method)
            if not arg_spec.args[0] == "self":
                raise SystemError_(
                    f"{location} Ask must have 'self' as first parameter."
                )
            if arg_spec.varargs:
                raise SystemError_(
                    f"{location} Ask cannot contain varargs."
                )
            if arg_spec.kwonlyargs:
                raise SystemError_(f"{location} Ask cannot contain kwargs.")
            if "return" in arg_spec.annotations:
                raise SystemError_(
                    f"{location} Ask cannot have return annotation."
                )
            if not all(
                arg in arg_spec.annotations for arg in arg_spec.args[1:]
            ):
                raise SystemError_(
                    f"{location} Ask parameters must be type-annotated."
                )

            arguments = cls.__extract_arguments(location, arg_spec)
            ask = Ask(definition, method_name, arguments)
            cls.asks[system][definition] = ask

            if ask.has_database_arguments:
                return cls.__database_resolver_method(method, ask)

            return method

        return gather

    @classmethod
    def __extract_arguments(
        cls, location: str, arg_spec
    ) -> t.Sequence[Argument]:
        arguments: t.List[Argument] = []
        has_optional_argument = False
        defaults = arg_spec.defaults or ()
        try:
            has_optional_argument = False
            for argument in arg_spec.args[1:]:  # Skipping self
                type_ = arg_spec.annotations[argument]

                if optional_type := cls.__extract_optional_type(type_):
                    if not has_optional_argument:
                        has_optional_argument = True
                        if not defaults or defaults != (
                            len(arg_spec.args)
                            - arg_spec.args.index(argument)
                        ) * (None,):
                            raise SystemError_(
                                f"{location} All optional arguments must"
                                " have None as a default value."
                            )

                    argument = Argument(
                        name=argument,
                        type_=optional_type,
                        is_optional=True,
                    )
                    arguments.append(argument)
                    continue

                if cls.__is_argument_type_allowed(type_):
                    if has_optional_argument:
                        raise SystemError_(
                            f"{location} Ask cannot have a required"
                            " parameter after an optional one."
                        )
                    argument = Argument(
                        name=argument,
                        type_=type_,
                        is_optional=False,
                    )
                    arguments.append(argument)
                    continue

                raise
        except SystemError_:
            raise
        except Exception:
            # The typing module's types do not work with 'issubclass',
            raise SystemError_(
                f"{location} Ask parameters can only be str, int or float,"
                " including optional."
            )

        if defaults and not has_optional_argument:
            raise SystemError_(
                f"{location} Required arguments cannot have default values."
            )

        return arguments

    @classmethod
    def __is_argument_type_allowed(cls, type_: t.Type) -> bool:
        return (
            issubclass(type_, (DatabaseRecord, str, int, float))
            and type_ is not bool  # bool subclasses int
        )

    @classmethod
    def __extract_optional_type(cls, type_: t.Type) -> t.Optional[t.Type]:
        if (
            isinstance(type_, t._UnionGenericAlias)  # type: ignore
            and len(type_.__args__) == 2
            and type_.__args__[1] is type(None)
            and cls.__is_argument_type_allowed(type_.__args__[0])
        ):
            return type_.__args__[0]
        return None

    @classmethod
    def __database_resolver_method(cls, method: t.Callable, ask: Ask):
        @functools.wraps(method)
        def resolver_method(system: System, *args):
            resolved_arguments: t.List[t.Any] = []
            for passed_argument, argument in zip(args, ask.arguments):
                type_ = argument.type_
                if issubclass(type_, DatabaseRecord):
                    id_ = ID(passed_argument)
                    database_object = system.database.retrieve(type_, id_)
                    if not argument.is_optional and not database_object:
                        raise SystemError_(
                            f"{type_.__name__} with id {id_!r} not found."
                        )
                    resolved_arguments.append(database_object)
                else:
                    resolved_arguments.append(passed_argument)

            return method(system, *resolved_arguments)

        return cls.mimic_method(resolver_method, method)

    @t.final
    def _handle_ask(self, requested_ask: str):
        if not (
            match := self.__match_ask(requested_ask, self.asks[BASE_SYSTEM])
            or self.__match_ask(requested_ask, self.asks[self.name])
        ):
            Typer.header(f"Ask {requested_ask!r} not found.")
            return

        ask, passed_arguments = match

        try:
            arguments = self.__parse_arguments(ask, passed_arguments)
        except (SystemError_, LinkerError) as error:
            Typer.header(str(error))
            return

        getattr(self, ask.method_name)(*arguments)

    @staticmethod
    def __match_ask(
        requested_ask: str,
        asks: t.Mapping[AskDefinition, Ask],
    ) -> t.Optional[t.Tuple[Ask, t.Tuple[str]]]:
        ask_components = requested_ask.split(" ")
        # Asks of two words are prioritised
        # For example, 'ls root' before 'ls'
        for i in range(2, 0, -1):
            if ask := asks.get(" ".join(ask_components[0:i])):
                return ask, tuple(ask_components[i:])
        return None

    @staticmethod
    def __parse_arguments(
        ask: Ask, passed_arguments: t.Sequence[str]
    ) -> t.Sequence[t.Any]:
        parsed_arguments: t.Sequence[t.Any] = []

        if len(passed_arguments) < len(
            [a for a in ask.arguments if not a.is_optional]
        ) or len(passed_arguments) > len(ask.arguments):
            required_arguments = (
                "Required: "
                + ", ".join(
                    [
                        f"{a.name}{'?' if a.is_optional else ''}"
                        for a in ask.arguments
                    ]
                )
                if ask.arguments
                else "None required"
            )
            raise SystemError_(
                f"Invalid number of arguments. {required_arguments}."
            )

        for index, argument in enumerate(passed_arguments):
            type_ = ask.arguments[index].type_

            if issubclass(type_, DatabaseRecord):
                id_ = Linker.resolve(type_, argument)
                parsed_arguments.append(id_)
                continue

            try:
                parsed_argument = type_(argument)
            except ValueError:
                raise SystemError_(
                    f"Invalid value {argument!r} for type {type_!r}."
                )
            parsed_arguments.append(parsed_argument)

        # Given that we check if the passed arguments are
        # at least as the number of required arguments,
        # here we provide a default of None for all the
        # optional arguments which were not provided
        while len(parsed_arguments) < len(ask.arguments):
            parsed_arguments.append(None)

        return parsed_arguments

    @staticmethod
    def mimic_method(
        function: t.Callable, mimicked: t.Callable
    ) -> t.Callable:
        function.__name__ = mimicked.__name__
        function.__doc__ = mimicked.__doc__
        function.__qualname__ = mimicked.__qualname__
        function.__annotations__ = mimicked.__annotations__
        function.__signature__ = inspect.signature(mimicked)
        function.__wrapped__ = mimicked
        return function


class System(SystemABC):
    def _on_start(self): ...

    @SystemABC.ask("cs")
    def _current_system(self):
        Typer.header(self.name)

    @SystemABC.ask("help")
    def _help(self):
        Typer.header(f"{self.name} asks:")

        try:
            Typer.list(list(self.asks[self.name].keys()), enumerated=False)
        except KeyError:
            Typer.body(f"{self.name} has no asks.")

        if self.name != BASE_SYSTEM:
            Typer.header("General asks:")
            Typer.list(
                list(self.asks[BASE_SYSTEM].keys()), enumerated=False
            )

    @SystemABC.ask("archive")
    def _archive(self): ...

    @SystemABC.ask("exit")
    def _exit(self):
        self.exit()

    @SystemABC.ask("farewell")
    def _adios(self):
        Typer.header("Farewell!", with_separator=True)
        sys.exit(0)

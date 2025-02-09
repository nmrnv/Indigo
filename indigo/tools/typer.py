import datetime
import os
import subprocess
import textwrap
import typing as t

from indigo.utils import date_utils

Type_ = t.TypeVar("Type_")

# Checking if there is a terminal as this could
# be ran from cron where there is not, so we're
# defaulting the cols value to 64.
if os.environ.get("TERM"):
    tput_cols = subprocess.check_output(["tput", "cols"])
    columns = int(tput_cols.decode("utf-8"))
else:
    columns = 64

INDENT = 4 if columns >= 78 else 2
WIDTH = 78 if columns >= 78 else columns - 2


class Typer:
    print_ = print
    input_ = input

    @classmethod
    def header(cls, line: str, with_separator: bool = False):
        cls.separator()
        cls.print_(cls._wrap(line))
        if with_separator:
            cls.separator()

    @classmethod
    def body(cls, line: str):
        cls.print_(cls._wrap(line))

    @classmethod
    def separator(cls):
        cls.print_("")

    @classmethod
    def list(
        cls,
        items: t.Sequence,
        enumerated: bool = True,
        title: t.Optional[str] = None,
        with_separator: bool = True,
        one_line: bool = False,
    ):
        if not title and with_separator:
            cls.separator()
        if title:
            cls.header(title)
        if not one_line or not enumerated:
            for index, item in enumerate(items):
                prefix = f"{index + 1}. " if enumerated else "– "
                cls.print_(cls._wrap(f"{prefix}{str(item)}"))
        else:
            items_strings = [
                f"{index + 1}.{str(item)}"
                for index, item in enumerate(items)
            ]
            cls.print_(cls._wrap("  ".join(items_strings)))

    @classmethod
    def input(
        cls,
        prompt: str,
        validator: t.Callable = bool,
        cancellable: bool = True,
        with_separator: bool = False,
    ) -> t.Optional[str]:
        if with_separator:
            cls.separator()
        input_ = None
        while not input_:
            input_ = cls.input_(
                cls._wrap(f"{prompt} ", drop_whitespace=False)
            )
        if cancellable and input_.lower() == "cancel":
            return None
        try:
            if not validator(input_):
                raise ValueError
        except ValueError:
            cls.separator()
            cls.body(f"Invalid value {input_!r}.")
            return cls.input(
                prompt,
                validator,
                cancellable,
            )
        return input_

    @classmethod
    def input_date(
        cls,
        prompt: str,
        with_separator: bool = False,
    ) -> t.Optional[datetime.datetime]:
        date_ = None
        while not date_:
            if not (
                date_str := cls.input(
                    prompt=prompt, with_separator=with_separator
                )
            ):
                return None
            if date_str.lower() == "today":
                return date_utils.today()
            elif date_str.lower() == "yesterday":
                return date_utils.yesterday()
            try:
                date_ = date_utils.date_from_str(date_str)
            except ValueError:
                cls.body(
                    f"Invalid date {date_str}. Accepted 'today',"
                    " 'yesterday', or 'dd/mm/yyyy' format."
                )
        return date_

    @classmethod
    def select(
        cls,
        options: t.Sequence[Type_],
        display_repr: t.Optional[t.Sequence[str]] = None,
        prompt: str = "Select item:",
        with_separator: bool = True,
        one_line: bool = False,
    ) -> t.Optional[Type_]:
        cls.header(prompt)
        if display_repr:
            if len(options) != len(display_repr):
                raise ValueError(
                    "Length of options must be equal to the display"
                    " representations"
                )
            cls.list(
                display_repr,
                with_separator=with_separator,
                one_line=one_line,
            )
        else:
            cls.list(
                list(map(str, options)),
                with_separator=with_separator,
                one_line=one_line,
            )

        option = None
        while not option:
            if not (
                selected_index := cls.input(
                    "Enter index:", with_separator=False
                )
            ):
                return None
            try:
                index = int(selected_index) - 1
                if index < 0 or index > len(options) - 1:
                    raise ValueError
                option = options[index]
            except (ValueError, IndexError):
                cls.body(f"Invalid index {selected_index!r}.")

        return option

    @classmethod
    def confirm(cls, prompt: t.Optional[str] = None) -> bool:
        option = cls.select(
            ["Yes", "No"],
            prompt=prompt or "Are you sure?",
            with_separator=False,
            one_line=True,
        )
        return option == "Yes"

    @classmethod
    def clear(cls):
        subprocess.run(["clear"])

    @classmethod
    def _wrap(cls, text: str, drop_whitespace: bool = True) -> str:
        initial_indent = INDENT
        subsequent_indent = INDENT + 2
        return textwrap.fill(
            text=text,
            width=WIDTH,
            initial_indent=initial_indent * " ",
            subsequent_indent=subsequent_indent * " ",
            drop_whitespace=drop_whitespace,
        )

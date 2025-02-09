from calendar import monthrange
from datetime import datetime, time, timedelta, timezone
from enum import Enum, unique
from zoneinfo import ZoneInfo

TIMEZONE_UTC = timezone.utc
TIMEZONE_UK = ZoneInfo("Europe/London")


def now(tz=TIMEZONE_UTC) -> datetime:
    # Rounding microseconds to 0 to replicate BSON's behaviour
    return datetime.now(tz=tz).replace(microsecond=0)


def today() -> datetime:
    return now().replace(hour=0, minute=0, second=0, microsecond=0)


def yesterday() -> datetime:
    return today() - timedelta(days=1)


def zeroed_datetime(
    year: int = 2020,
    month: int = 1,
    day: int = 1,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    microsecond: int = 0,
    tz=TIMEZONE_UTC,
) -> datetime:
    return datetime(year, month, day, hour, minute, second, microsecond, tz)


def date_from_str(date_str_: str) -> datetime:
    date_ = datetime.strptime(date_str_, "%d/%m/%Y").date()
    return datetime.combine(date_, time(tzinfo=TIMEZONE_UTC))


def time_from_str(time_: str) -> time:
    for format_ in ["%M:%S", "%H:%M:%S"]:
        try:
            return datetime.strptime(time_, format_).time()
        except ValueError:
            continue
    raise ValueError(
        f"time data {time_!r} does not match formats '%M:%S' and '%H:%M:%S'"
    )


def time_to_seconds(time_: time) -> int:
    return time_.hour * 60 * 60 + time_.minute * 60 + time_.second


def from_iso(iso_str: str) -> datetime:
    return datetime.fromisoformat(iso_str)


def to_iso(date_: datetime) -> str:
    return date_.isoformat()


def from_timestamp(timestamp: float) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=TIMEZONE_UTC)


def beginning_of_day(date_: datetime = None) -> datetime:
    date_ = date_ if date_ else now()
    return date_.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(date_: datetime = None) -> datetime:
    date_ = date_ if date_ else now()
    return beginning_of_day(date_) + timedelta(
        hours=23, minutes=59, seconds=59
    )


def beginning_of_week(date_: datetime = None) -> datetime:
    date_ = date_ if date_ else now()
    monday = date_ - timedelta(days=date_.weekday())
    return beginning_of_day(monday)


def end_of_week(date_: datetime = None) -> datetime:
    date_ = date_ if date_ else now()
    sunday = beginning_of_week(date_) + timedelta(days=6)
    return end_of_day(sunday)


def beginning_of_month(date_: datetime = None) -> datetime:
    date_ = date_ if date_ else now()
    return beginning_of_day(date_.replace(day=1))


def end_of_month(date_: datetime = None) -> datetime:
    date_ = date_ if date_ else now()
    number_of_days = monthrange(date_.year, date_.month)[1]
    last_day_of_the_month = beginning_of_month(date_).replace(
        day=number_of_days
    )
    return end_of_day(last_day_of_the_month)


def get_quarter(date_: datetime = None) -> int:
    date_ = date_ if date_ else now()
    return (date_.month - 1) // 3 + 1


def beginning_of_quarter(date_: datetime = None) -> datetime:
    date_ = date_ if date_ else now()
    starting_month = (get_quarter(date_) - 1) * 3 + 1
    return beginning_of_day(
        datetime(
            date_.year, month=starting_month, day=1, tzinfo=date_.tzinfo
        )
    )


def end_of_quarter(date_: datetime = None) -> datetime:
    date_ = date_ if date_ else now()
    starting_month = (get_quarter(date_) - 1) * 3 + 1
    ending_month = starting_month + 2
    number_of_days = monthrange(date_.year, ending_month)[1]
    return end_of_day(
        datetime(
            date_.year,
            month=ending_month,
            day=number_of_days,
            tzinfo=date_.tzinfo,
        )
    )


def beginning_of_year(date_: datetime = None) -> datetime:
    date_ = date_ if date_ else now()
    return beginning_of_day(date_).replace(month=1, day=1)


def end_of_year(date_: datetime = None) -> datetime:
    date_ = date_ if date_ else now()
    return end_of_day(date_).replace(month=12, day=31)


def are_on_the_same_day(date_: datetime, compared: datetime) -> bool:
    return (
        date_.year == compared.year
        and date_.month == compared.month
        and date_.day == compared.day
    )


def are_in_the_same_month(date_: datetime, compared: datetime) -> bool:
    return date_.year == compared.year and date_.month == compared.month


def time_str(datetime_: datetime) -> str:
    format_str = "%H:%M"
    return datetime_.astimezone(TIMEZONE_UK).strftime(format_str)


def date_str(date_: datetime, worded=True) -> str:
    today_ = today()
    if worded and are_on_the_same_day(date_, today_):
        return "Today"
    elif worded and are_on_the_same_day(date_, today_ - timedelta(days=1)):
        return "Yesterday"
    elif worded and are_on_the_same_day(date_, today_ + timedelta(days=1)):
        return "Tomorrow"
    else:
        format_str = "%d/%m/%Y"
        return date_.astimezone(TIMEZONE_UK).strftime(format_str)


def month_str(date_: datetime) -> str:
    format_str = "%Y.%m"
    return date_.astimezone(TIMEZONE_UK).strftime(format_str)


def date_range_str(from_: datetime, to: datetime) -> str:
    return (
        f"{date_str(from_, worded=False)} to {date_str(to, worded=False)}"
        if not are_on_the_same_day(from_, to)
        else f"{date_str(from_)}"
    )


def datetime_str(datetime_: datetime) -> str:
    format_str = "%H:%M %d/%m/%Y"
    return datetime_.astimezone(TIMEZONE_UK).strftime(format_str)


def minutes_to_rounded_half_hours_str(minutes: float) -> str:
    hours = round(minutes / 60 * 2) / 2
    if hours % 1 == 0:
        return f"{int(hours)}h"
    return f"{hours}h"


def duration_str(minutes: int, without_days: bool = True) -> str:
    if isinstance(minutes, float):
        minutes = round(minutes)
    if minutes == 1:
        return f"{minutes} minute"
    elif minutes < 60:
        return f"{minutes} minutes"
    else:
        hours, minutes = divmod(minutes, 60)
        parts = []
        if not without_days:
            days, hours = divmod(hours, 24)
            parts.append((days, "days"))
        parts.extend([(hours, "hours"), (minutes, "minutes")])
        components = []
        for value, display in parts:
            if value == 0:
                continue
            if value == 1:
                display = display[:-1]
            components.append(f"{value} {display}")
        return " ".join(components)


@unique
class Weekday(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"

    @property
    def abbreviated(self) -> str:
        return self.name[:3].upper()

    @classmethod
    def from_abbreviated(cls, abbreviated: str) -> "Weekday":
        weekday_lower = abbreviated.lower()
        for weekday in cls:
            if weekday_lower == weekday[:3]:
                return Weekday(weekday)
        raise ValueError(f"Invalid weekday abbreviation {abbreviated!r}.")

    @property
    def index_(self) -> int:
        return list(Weekday).index(self)

    @classmethod
    def from_index(cls, index: int) -> "Weekday":
        try:
            return Weekday(list(Weekday)[index])
        except IndexError:
            raise ValueError(f"Invalid weekday index {index!r}.")


class Month(str, Enum):
    JANUARY = "january"
    FEBRUARY = "february"
    MARCH = "march"
    APRIL = "april"
    MAY = "may"
    JUNE = "june"
    JULY = "july"
    AUGUST = "august"
    SEPTEMBER = "september"
    OCTOBER = "october"
    NOVEMBER = "november"
    DECEMBER = "december"

    @property
    def index_(self) -> int:
        return list(Month).index(self) + 1

    @classmethod
    def from_index(cls, index: int) -> "Month":
        try:
            return Month(list(Month)[index - 1])
        except IndexError:
            raise ValueError(f"Invalid month index {index!r}.")

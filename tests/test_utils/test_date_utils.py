from datetime import datetime, time, timedelta, timezone

import pytest
from freezegun import freeze_time

from indigo.utils import date_utils
from indigo.utils.date_utils import TIMEZONE_UTC, Month, Weekday


@freeze_time("2021-11-11T04:51:52.000052+00:00")
def test_now():
    assert date_utils.now() == datetime(
        year=2021,
        month=11,
        day=11,
        hour=4,
        minute=51,
        second=52,
        microsecond=0,
        tzinfo=timezone.utc,
    )


def test_today():
    assert date_utils.today() == datetime.now(tz=timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def test_yesterday():
    assert date_utils.yesterday() == datetime.now(tz=timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(days=1)


def test_zeroed_datetime():
    assert date_utils.zeroed_datetime() == datetime(
        2020, 1, 1, 0, 0, 0, 0, timezone.utc
    )


def test_date_from_str():
    # When
    date_ = date_utils.date_from_str("21/08/2021")

    # Then
    assert date_ == datetime(
        day=21, month=8, year=2021, tzinfo=TIMEZONE_UTC
    )


def test_time_from_str():
    # When
    time_ = date_utils.time_from_str("1:25:33")

    # Then
    assert time_ == time(hour=1, minute=25, second=33)

    # When
    time_ = date_utils.time_from_str("01:25:33")

    # Then
    assert time_ == time(hour=1, minute=25, second=33)

    # When
    time_ = date_utils.time_from_str("25:33")

    # Then
    assert time_ == time(hour=0, minute=25, second=33)

    # When
    time_ = date_utils.time_from_str("05:33")

    # Then
    assert time_ == time(hour=0, minute=5, second=33)

    # When
    time_ = date_utils.time_from_str("5:03")

    # Then
    assert time_ == time(hour=0, minute=5, second=3)


def test_time_from_str_failures():
    # Then
    with pytest.raises(ValueError):
        # When
        date_utils.time_from_str("invalid_time")


@pytest.mark.parametrize(
    "time_, seconds",
    [
        (
            time(hour=1, minute=2, second=3, microsecond=5),
            60 * 60 + 2 * 60 + 3,
        ),
        (time(hour=2, second=3, microsecond=5), 120 * 60 + 3),
        (time(minute=2, second=3, microsecond=5), 2 * 60 + 3),
        (time(hour=1), 60 * 60),
        (time(minute=5), 5 * 60),
        (time(second=10), 10),
    ],
)
def test_time_to_seconds(time_: time, seconds: int):
    # Then
    assert date_utils.time_to_seconds(time_) == seconds


def test_from_iso():
    # When
    iso_str = "2021-11-11T04:51:52.000052+00:00"
    date_ = date_utils.from_iso(iso_str)

    # Then
    assert date_ == datetime(
        year=2021,
        month=11,
        day=11,
        hour=4,
        minute=51,
        second=52,
        microsecond=52,
        tzinfo=timezone.utc,
    )


@freeze_time("2021-11-11T04:51:52.000052+00:00")
def test_to_iso():
    # Given
    date_ = date_utils.now()

    # Then
    assert date_utils.to_iso(date_) == "2021-11-11T04:51:52+00:00"


@freeze_time("2021-11-11T04:51:52+00:00")
def test_from_timestamp():
    # Then
    assert date_utils.from_timestamp(1636606312) == datetime(
        year=2021,
        month=11,
        day=11,
        hour=4,
        minute=51,
        second=52,
        tzinfo=timezone.utc,
    )


@freeze_time("2021-11-11 04:51:52+00:00")
def test_beginning_of_day():
    # Given
    now = date_utils.now()

    # Then (now is the default argument)
    assert date_utils.beginning_of_day() == datetime(
        year=2021,
        month=11,
        day=11,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    yesterday = now - timedelta(days=1)

    # Then
    assert date_utils.beginning_of_day(yesterday) == datetime(
        year=2021,
        month=11,
        day=10,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    iso_str = "2019-08-21T04:51:52.000052+00:00"
    past_date = date_utils.from_iso(iso_str)

    # Then
    assert date_utils.beginning_of_day(past_date) == datetime(
        year=2019,
        month=8,
        day=21,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=timezone.utc,
    )


@freeze_time("2021-11-11 04:51:52+00:00")
def test_end_of_day():
    # Given
    now = date_utils.now()

    # Then (now is the default argument)
    assert date_utils.end_of_day() == datetime(
        year=2021,
        month=11,
        day=11,
        hour=23,
        minute=59,
        second=59,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    yesterday = now - timedelta(days=1)

    # Then
    assert date_utils.end_of_day(yesterday) == datetime(
        year=2021,
        month=11,
        day=10,
        hour=23,
        minute=59,
        second=59,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    iso_str = "2019-08-21T04:51:52.000052+00:00"
    past_date = date_utils.from_iso(iso_str)

    # Then
    assert date_utils.end_of_day(past_date) == datetime(
        year=2019,
        month=8,
        day=21,
        hour=23,
        minute=59,
        second=59,
        microsecond=0,
        tzinfo=timezone.utc,
    )


def test_beginning_of_week():
    # Given
    now = date_utils.from_iso("2021-11-11 04:51:52+00:00")

    # Then (now is the default argument)
    assert date_utils.beginning_of_week(now) == datetime(
        year=2021,
        month=11,
        day=8,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    two_weeks_ago = now - timedelta(weeks=2)

    # Then
    assert date_utils.beginning_of_week(two_weeks_ago) == datetime(
        year=2021,
        month=10,
        day=25,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    iso_str = "2019-08-21T04:51:52.000052+00:00"
    past_date = date_utils.from_iso(iso_str)

    # Then
    assert date_utils.beginning_of_week(past_date) == datetime(
        year=2019,
        month=8,
        day=19,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=timezone.utc,
    )


def test_end_of_week():
    # Given
    now = date_utils.from_iso("2021-11-11 04:51:52+00:00")

    # Then (now is the default argument)
    assert date_utils.end_of_week(now) == datetime(
        year=2021,
        month=11,
        day=14,
        hour=23,
        minute=59,
        second=59,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    two_weeks_ago = now - timedelta(weeks=2)

    # Then
    assert date_utils.end_of_week(two_weeks_ago) == datetime(
        year=2021,
        month=10,
        day=31,
        hour=23,
        minute=59,
        second=59,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    iso_str = "2019-08-21T04:51:52.000052+00:00"
    past_date = date_utils.from_iso(iso_str)

    # Then
    assert date_utils.end_of_week(past_date) == datetime(
        year=2019,
        month=8,
        day=25,
        hour=23,
        minute=59,
        second=59,
        microsecond=0,
        tzinfo=timezone.utc,
    )


@freeze_time("2021-11-11 04:51:52+00:00")
def test_beginning_of_month():
    # Given
    now = date_utils.now()

    # Then (now is the default argument)
    assert date_utils.beginning_of_month() == datetime(
        year=2021,
        month=11,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    last_month = now.replace(month=10)

    # Then
    assert date_utils.beginning_of_month(last_month) == datetime(
        year=2021,
        month=10,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    iso_str = "2019-08-21T04:51:52.000052+00:00"
    past_date = date_utils.from_iso(iso_str)

    # Then
    assert date_utils.beginning_of_month(past_date) == datetime(
        year=2019,
        month=8,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=timezone.utc,
    )


@freeze_time("2021-11-11 04:51:52+00:00")
def test_end_of_month():
    # Given
    now = date_utils.now()

    # Then (now is the default argument)
    assert date_utils.end_of_month() == datetime(
        year=2021,
        month=11,
        day=30,
        hour=23,
        minute=59,
        second=59,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    last_month = now.replace(month=10)

    # Then
    assert date_utils.end_of_month(last_month) == datetime(
        year=2021,
        month=10,
        day=31,
        hour=23,
        minute=59,
        second=59,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    iso_str = "2019-08-21T04:51:52.000052+00:00"
    past_date = date_utils.from_iso(iso_str)

    # Then
    assert date_utils.end_of_month(past_date) == datetime(
        year=2019,
        month=8,
        day=31,
        hour=23,
        minute=59,
        second=59,
        microsecond=0,
        tzinfo=timezone.utc,
    )


@freeze_time("2021-11-11 04:51:52+00:00")
def test_get_quarter():
    # Given
    now = date_utils.now()

    # Then
    assert date_utils.get_quarter() == 4

    # Given
    quarter_by_month = {
        1: 1,
        2: 1,
        3: 1,
        4: 2,
        5: 2,
        6: 2,
        7: 3,
        8: 3,
        9: 3,
        10: 4,
        11: 4,
        12: 4,
    }

    for month in range(1, 13):
        now = now.replace(month=month)
        # Then
        assert date_utils.get_quarter(now) == quarter_by_month[month]


@freeze_time("2021-11-11 04:51:52+00:00")
def test_beginning_of_quarter():
    # Given
    now = date_utils.now()

    # Then (now is the default argument)
    assert date_utils.beginning_of_quarter() == datetime(
        year=2021,
        month=10,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    last_quarter = now.replace(month=8)

    # Then
    assert date_utils.beginning_of_quarter(last_quarter) == datetime(
        year=2021,
        month=7,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    iso_str = "2019-01-03T04:51:52.000052+00:00"
    past_date = date_utils.from_iso(iso_str)

    # Then
    assert date_utils.beginning_of_quarter(past_date) == datetime(
        year=2019,
        month=1,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=timezone.utc,
    )


@freeze_time("2021-11-11 04:51:52+00:00")
def test_end_of_quarter():
    # Given
    now = date_utils.now()

    # Then (now is the default argument)
    assert date_utils.end_of_quarter() == datetime(
        year=2021,
        month=12,
        day=31,
        hour=23,
        minute=59,
        second=59,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    last_quarter = now.replace(month=8)

    # Then
    assert date_utils.end_of_quarter(last_quarter) == datetime(
        year=2021,
        month=9,
        day=30,
        hour=23,
        minute=59,
        second=59,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    iso_str = "2019-01-03T04:51:52.000052+00:00"
    past_date = date_utils.from_iso(iso_str)

    # Then
    assert date_utils.end_of_quarter(past_date) == datetime(
        year=2019,
        month=3,
        day=31,
        hour=23,
        minute=59,
        second=59,
        microsecond=0,
        tzinfo=timezone.utc,
    )


@freeze_time("2021-11-11 04:51:52+00:00")
def test_beginning_of_year():
    # Given
    now = date_utils.now()

    # Then (now is the default argument)
    assert date_utils.beginning_of_year() == datetime(
        year=2021,
        month=1,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    last_year = now.replace(year=now.year - 1)

    # Then
    assert date_utils.beginning_of_year(last_year) == datetime(
        year=2020,
        month=1,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    iso_str = "2019-01-03T04:51:52.000052+00:00"
    past_date = date_utils.from_iso(iso_str)

    # Then
    assert date_utils.beginning_of_year(past_date) == datetime(
        year=2019,
        month=1,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=timezone.utc,
    )


@freeze_time("2021-11-11 04:51:52+00:00")
def test_end_of_year():
    # Given
    now = date_utils.now()

    # Then (now is the default argument)
    assert date_utils.end_of_year() == datetime(
        year=2021,
        month=12,
        day=31,
        hour=23,
        minute=59,
        second=59,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    last_year = now.replace(year=now.year - 1)

    # Then
    assert date_utils.end_of_year(last_year) == datetime(
        year=2020,
        month=12,
        day=31,
        hour=23,
        minute=59,
        second=59,
        microsecond=0,
        tzinfo=timezone.utc,
    )

    # Given
    iso_str = "2019-01-03T04:51:52.000052+00:00"
    past_date = date_utils.from_iso(iso_str)

    # Then
    assert date_utils.end_of_year(past_date) == datetime(
        year=2019,
        month=12,
        day=31,
        hour=23,
        minute=59,
        second=59,
        microsecond=0,
        tzinfo=timezone.utc,
    )


@freeze_time("2021-11-11 04:51:52+00:00")
def test_are_on_the_same_day():
    # Given
    now = date_utils.now()

    # Then
    assert date_utils.are_on_the_same_day(now, now)

    # Given
    some_time_ago = now.replace(hour=1, minute=2, microsecond=3)

    # Then
    assert date_utils.are_on_the_same_day(now, some_time_ago)

    # Given
    yesterday = now - timedelta(days=1)

    # Then
    assert not date_utils.are_on_the_same_day(now, yesterday)

    # Given
    last_month = now.replace(month=now.month - 1)

    # Then
    assert not date_utils.are_on_the_same_day(now, last_month)

    # Given
    yesteryear = now.replace(year=now.year - 1)

    # Then
    assert not date_utils.are_on_the_same_day(now, yesteryear)

    # Given
    some_past_day = now.replace(year=2019, month=8, day=21)

    # Then
    assert not date_utils.are_on_the_same_day(now, some_past_day)


@freeze_time("2021-11-11 04:51:52+00:00")
def test_are_in_the_same_month():
    # Given
    now = date_utils.now()

    # Then
    assert date_utils.are_in_the_same_month(now, now)

    # Given
    some_time_ago_today = now.replace(hour=1, minute=2, microsecond=3)

    # Then
    assert date_utils.are_in_the_same_month(now, some_time_ago_today)

    # Given
    yesterday = now - timedelta(days=1)

    # Then
    assert date_utils.are_in_the_same_month(now, yesterday)

    # Given
    last_month = now.replace(month=now.month - 1)

    # Then
    assert not date_utils.are_in_the_same_month(now, last_month)

    # Given
    yesteryear = now.replace(year=now.year - 1)

    # Then
    assert not date_utils.are_in_the_same_month(now, yesteryear)

    # Given
    some_past_day = now.replace(year=2019, month=8, day=21)

    # Then
    assert not date_utils.are_in_the_same_month(now, some_past_day)


@freeze_time("2021-11-11 04:51:52+00:00")
def test_time_str():
    # Given
    now = date_utils.now()

    # Then
    assert date_utils.time_str(now) == "04:51"


@freeze_time("2022-10-11 04:51:52+00:00")
def test_time_str_localised():
    # Given
    now = date_utils.now()

    # Then
    assert date_utils.time_str(now) == "05:51"


@freeze_time("2021-11-21 04:51:52+00:00")
def test_date_str():
    # Given
    now = date_utils.now()

    # Then
    assert date_utils.date_str(now) == "Today"
    assert date_utils.date_str(now, worded=False) == "21/11/2021"

    # Given
    tomorrow = now + timedelta(days=1)

    # Then
    assert date_utils.date_str(tomorrow) == "Tomorrow"
    assert date_utils.date_str(tomorrow, worded=False) == "22/11/2021"

    # Given
    yesterday = now - timedelta(days=1)

    # Then
    assert date_utils.date_str(yesterday) == "Yesterday"
    assert date_utils.date_str(yesterday, worded=False) == "20/11/2021"

    # Given
    past_date = now - timedelta(days=2)

    # Then
    assert date_utils.date_str(past_date) == "19/11/2021"
    assert date_utils.date_str(past_date, worded=False) == "19/11/2021"


@freeze_time("2022-10-10 23:51:52+00:00")
def test_date_str_localised():
    # Given
    now = date_utils.now()

    # Then
    assert date_utils.date_str(now, worded=False) == "11/10/2022"


@freeze_time("2021-11-21 04:51:52+00:00")
def test_month_str():
    assert date_utils.month_str(date_utils.today()) == "2021.11"


@freeze_time("2021-09-30 23:51:52+00:00")
def test_month_str_localised():
    # Given
    now = date_utils.now()

    # Then
    assert date_utils.month_str(now) == "2021.10"


def test_date_range_str():
    # Given
    from_date = date_utils.date_from_str("21/08/2021")
    to_date = date_utils.date_from_str("21/08/2022")

    # Then
    assert (
        date_utils.date_range_str(from_date, to_date)
        == "21/08/2021 to 21/08/2022"
    )
    assert date_utils.date_range_str(from_date, from_date) == "21/08/2021"


@freeze_time("2021-11-11 04:51:52+00:00")
def test_datetime_str():
    # Given
    now = date_utils.now()

    # Then
    assert date_utils.datetime_str(now) == "04:51 11/11/2021"


@pytest.mark.parametrize(
    "given, expected",
    [
        ("2022-09-28 04:51:52+00:00", "05:51 28/09/2022"),
        ("2022-09-29 23:51:52+00:00", "00:51 30/09/2022"),
        ("2022-09-30 23:51:52+00:00", "00:51 01/10/2022"),
    ],
)
def test_datetime_str_localised(given, expected, frozen_time):
    # Given
    frozen_time.move_to(given)
    now = date_utils.now()

    # Then
    assert date_utils.datetime_str(now) == expected


@pytest.mark.parametrize(
    "minutes, without_days, expected_output",
    [
        (1, True, "1 minute"),
        (30, False, "30 minutes"),
        (60, True, "1 hour"),
        (61, False, "1 hour 1 minute"),
        (80, True, "1 hour 20 minutes"),
        (140, False, "2 hours 20 minutes"),
        (48 * 60, True, "48 hours"),
        (48 * 60 + 122, True, "50 hours 2 minutes"),
        (24 * 60, False, "1 day"),
        (24 * 60 + 1, False, "1 day 1 minute"),
        (24 * 60 + 120, False, "1 day 2 hours"),
        (48 * 60 + 122, False, "2 days 2 hours 2 minutes"),
    ],
)
def test_duration_str(
    minutes: int, without_days: bool, expected_output: str
):
    # Then
    assert (
        date_utils.duration_str(minutes, without_days=without_days)
        == expected_output
    )


@pytest.mark.parametrize(
    "minutes, expected_output",
    [(14, "0h"), (20, "0.5h"), (30, "0.5h"), (55, "1h")],
)
def test_minutes_to_rounded_half_hours_str(
    minutes: int, expected_output: str
):
    # Then
    assert (
        date_utils.minutes_to_rounded_half_hours_str(minutes)
        == expected_output
    )


@pytest.mark.parametrize(
    "weekday, abbreviation",
    [
        (Weekday.MONDAY, "MON"),
        (Weekday.TUESDAY, "TUE"),
        (Weekday.WEDNESDAY, "WED"),
        (Weekday.THURSDAY, "THU"),
        (Weekday.FRIDAY, "FRI"),
        (Weekday.SATURDAY, "SAT"),
        (Weekday.SUNDAY, "SUN"),
    ],
)
def test_weekday_abbreviated(weekday: Weekday, abbreviation: str):
    # Then
    assert weekday.abbreviated == abbreviation
    assert Weekday.from_abbreviated(abbreviation) == weekday


def test_weekday_abbreviated_failure():
    # Then
    with pytest.raises(
        ValueError, match="Invalid weekday abbreviation 'INV'"
    ):
        # When
        Weekday.from_abbreviated("INV")


@pytest.mark.parametrize(
    "weekday, index",
    [
        (Weekday.MONDAY, 0),
        (Weekday.TUESDAY, 1),
        (Weekday.WEDNESDAY, 2),
        (Weekday.THURSDAY, 3),
        (Weekday.FRIDAY, 4),
        (Weekday.SATURDAY, 5),
        (Weekday.SUNDAY, 6),
    ],
)
def test_weekday_index(weekday: Weekday, index: int):
    # Then
    assert weekday.index_ == index
    assert Weekday.from_index(index) == weekday


def test_weekday_index_failure():
    # Then
    with pytest.raises(ValueError, match="Invalid weekday index 7"):
        # When
        Weekday.from_index(7)


@pytest.mark.parametrize(
    "month, index",
    [
        (Month.JANUARY, 1),
        (Month.FEBRUARY, 2),
        (Month.MARCH, 3),
        (Month.APRIL, 4),
        (Month.MAY, 5),
        (Month.JUNE, 6),
        (Month.JULY, 7),
        (Month.AUGUST, 8),
        (Month.SEPTEMBER, 9),
        (Month.OCTOBER, 10),
        (Month.NOVEMBER, 11),
        (Month.DECEMBER, 12),
    ],
)
def test_month_index(month: Month, index: int):
    # Then
    assert month.index_ == index
    assert Month.from_index(index) == month


def test_month_index_failure():
    # Then
    with pytest.raises(ValueError, match="Invalid month index 13"):
        # When
        Month.from_index(13)

import time
from datetime import datetime, timedelta, timezone
from pydantic.datetime_parse import parse_date
from datetime import date
from typing import Any

import pytz

PERIOD_DAY = 0
PERIOD_WEEK = 1
PERIOD_MONTH = 2

PERIOD_CURRENT_WEEK = "Current Week"
PERIOD_LAST_WEEK = "Last Week"
PERIOD_LAST_4WEEK = "Last 4 Weeks"

# Monday based weeks
START_CURRENT_WEEK = "Current Week"
START_LAST_WEEK = "Last Week"
START_CUSTOM_WEEK = "Custom Week"

START_1WEEK = "1 Week"
START_2WEEK = "2 Week"
START_1MONTH = "1 Month"
START_3MONTHS = "3 Months"
START_6MONTHS = "6 Months"
START_12MONTHS = "12 Months"
START_24MONTHS = "24 Months"
START_ALL = "All"

LIST_START_WEEK_BY_MONDAY = [
    START_CURRENT_WEEK,
    START_LAST_WEEK,
    START_CUSTOM_WEEK,
]

LIST_START_WEEK_ONLY = [
    START_1WEEK,
    START_2WEEK,
]

LIST_START_WEEK_ONLY = LIST_START_WEEK_ONLY + LIST_START_WEEK_BY_MONDAY

LIST_ALL_START_PERIODS = [
    START_CURRENT_WEEK,
    START_LAST_WEEK,
    START_1WEEK,
    START_2WEEK,
    START_1MONTH,
    START_3MONTHS,
    START_6MONTHS,
    START_12MONTHS,
    START_24MONTHS,
]

# Just the period in use by the FEs
LIST_ACTIVE_START_PERIODS = [
    START_CURRENT_WEEK,
    START_LAST_WEEK,
    START_1MONTH,
    START_3MONTHS,
    START_6MONTHS,
    START_12MONTHS,
    START_24MONTHS,
]

YEAR_DAYS = 365


def getToday(tz):
    tz = pytz.timezone(tz)
    return datetime.now(tz)

def convert_local_to_utc(ts, format="%Y-%m-%d %H:%M:%S"):
    dt = datetime.strptime(ts, format)
    return dt.astimezone(timezone.utc).isoformat()


def add_tz(ts, tz, format="%Y-%m-%d %H:%M:%S"):
    try:
        if not isinstance(ts, datetime):
            ts = datetime.strptime(ts, format)
        localtz = pytz.timezone(tz)
        return localtz.localize(ts).isoformat()
    except Exception:
        pass
    return ts


def get_months_back(start):
    if start == START_ALL:
        return None

    if start == START_1MONTH:
        return 1
    elif start == START_3MONTHS:
        return 3
    elif start == START_6MONTHS:
        return 6
    elif start == START_12MONTHS:
        return 12
    elif start == START_24MONTHS:
        return 24

    return None


def get_days_from_monday_back(tz, start):
    monday_date = get_start_date(tz, start)
    start_date = getToday(tz)
    return (start_date - monday_date).days


def get_monday_back(d):
    if d.weekday() > 0:
        d = d + timedelta(days=-d.weekday())
    return d


def get_start_date(tz, start, round_to_month=False, base_date=None):
    if start == START_ALL or start is None or len(start) == 0:
        return None

    start_date = getToday(tz)

    if base_date:
        start_date = base_date

    if start == START_CURRENT_WEEK:
        start_date = get_monday_back(start_date)
    elif start == START_LAST_WEEK:
        start_date = get_monday_back(start_date + timedelta(days=-7))
    elif start == START_1WEEK:
        start_date = start_date + timedelta(days=-7)
    elif start == START_2WEEK:
        start_date = start_date + timedelta(days=-14)
    elif start == START_1MONTH:
        start_date = start_date + timedelta(days=-int(YEAR_DAYS / 12))
    elif start == START_3MONTHS:
        start_date = start_date + timedelta(days=-int(YEAR_DAYS / 4))
    elif start == START_6MONTHS:
        start_date = start_date + timedelta(days=-int(YEAR_DAYS / 2))
    elif start == START_12MONTHS:
        start_date = start_date + timedelta(days=-YEAR_DAYS)
    elif start == START_24MONTHS:
        start_date = start_date + timedelta(days=-int(YEAR_DAYS * 2))

    if round_to_month:
        start_date = start_date.replace(day=1)

    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    return start_date


def get_start_date_absolute(tz, start):
    
    if start == START_ALL:
        return None

    start_date = getToday(tz)

    if start == START_CURRENT_WEEK:
        start_date = get_monday_back(start_date)
    elif start == START_LAST_WEEK:
        start_date = get_monday_back(start_date + timedelta(days=-7))
    elif start == START_1WEEK:
        start_date = start_date + timedelta(days=-7)
    elif start == START_2WEEK:
        start_date = start_date + timedelta(days=-14)
    elif start == START_1MONTH:
        start_date = start_date + timedelta(days=-int(YEAR_DAYS / 12))
    elif start == START_3MONTHS:
        start_date = start_date + timedelta(days=-int(YEAR_DAYS / 4))
    elif start == START_6MONTHS:
        start_date = start_date + timedelta(days=-int(YEAR_DAYS / 2))
    elif start == START_12MONTHS:
        start_date = start_date + timedelta(days=-YEAR_DAYS)
    elif start == START_24MONTHS:
        start_date = start_date + timedelta(days=-int(YEAR_DAYS * 2))
    else:
        return None

    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    return start_date


def get_date_back(tz, days, hours=0):
    date = getToday(tz) + timedelta(days=-days, hours=-hours)

    # Move to the end to the day
    if hours == 0:
        date = date.replace(hour=23, minute=59, second=59, microsecond=0)

    return date


def get_period_format(period):
    group = "%Y-%m"

    if period == PERIOD_DAY:
        group = "%Y-%m-%d"
    elif period == PERIOD_WEEK:
        group = "%Y-%m"
    elif period == PERIOD_MONTH:
        group = "%Y-%m"

    return group


class DurationTimer(object):
    def __init__(self):
        self.started = time.time()
        self.stopped = 0

    def start(self):
        self.started = time.time()
        self.stopped = 0
        return self

    def stop(self):
        if self.started > 0:
            self.stopped = time.time()
        return self

    def duration(self):
        if self.stopped == 0:
            self.stopped = time.time()
        return int(round((self.stopped - self.started) * 1000, 0))

    def __str__(self):
        # if self.started == 0:
        #     return 'not-running'
        # if self.started > 0 and self.stopped == 0:
        #     return 'started: %d (running)' % self.started
        return DurationTimer.formatTime(self.duration())

    @staticmethod
    # convert to a readable string
    def formatTime(durationMS):
        if durationMS < 1000:
            return "%d millisecond(s)" % durationMS
        if durationMS < 60 * 1000:
            return "%d second(s)" % int(durationMS / 1000)
        min = int(durationMS / (60 * 1000))
        sec = int((durationMS - (min * 60 * 1000)) / 1000)
        if sec == 0:
            return "{MIN} minute(s)".format(MIN=min)
        return "{MIN} minute(s) {SEC} second(s)".format(MIN=min, SEC=sec)


################################
# API Param Helper


class utc_datetime(datetime):
    @classmethod
    def __get_validators__(cls):
        # yield parse_datetime  # default pydantic behavior
        yield cls.ensure_tzinfo

    @classmethod
    def ensure_tzinfo(cls, v):
        # if TZ isn't provided, we assume UTC, but you can do w/e you need
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        # else we convert to utc
        return v.astimezone(timezone.utc)

    @staticmethod
    def to_str(dt: datetime) -> str:
        return dt.isoformat()  # replace with w/e format you want# Simple Date


def validate_date(v: Any) -> date:
    return parse_date(v)


class StrictDate(date):
    @classmethod
    def __get_validators__(cls):
        yield validate_date

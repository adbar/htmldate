# pylint:disable-msg=E0611,I1101
"""
Filters for date parsing and date validators.
"""

import logging
import re

from collections import Counter
from collections.abc import Iterable
from datetime import datetime

from .settings import MIN_DATE
from .utils import Extractor

LOGGER = logging.getLogger(__name__)
LOGGER.debug("minimum date setting: %s", MIN_DATE)


def validate(
    dateobject: datetime | None, earliest: datetime, latest: datetime
) -> datetime | None:
    "Return the date if it falls within the time boundaries."
    if dateobject is None or not earliest.year <= dateobject.year <= latest.year:
        return None
    try:
        valid = earliest.timestamp() <= dateobject.timestamp() <= latest.timestamp()
    # Windows: no timestamps for naive dates before 1970
    except OSError:
        valid = (
            earliest.replace(tzinfo=None)
            <= dateobject.replace(tzinfo=None)
            <= latest.replace(tzinfo=None)
        )
    if not valid:
        LOGGER.debug("date not valid: %s", dateobject)
    return dateobject if valid else None


def validate_ymd(
    date_input: str, earliest: datetime, latest: datetime
) -> datetime | None:
    "Read a YYYY-MM-DD string, then validate it."
    try:
        # positional read: faster than strptime, separator-agnostic
        dateobject = datetime(
            int(date_input[:4]), int(date_input[5:7]), int(date_input[8:10])
        )
    except ValueError:
        # unpadded parts ("2020-1-15")
        try:
            dateobject = datetime.strptime(date_input, "%Y-%m-%d")
        except ValueError:
            return None
    return validate(dateobject, earliest, latest)


def is_valid_format(outputformat: str) -> bool:
    """Validate the output format in the settings"""
    # test with date object
    dateobject = datetime(2017, 9, 1, 0, 0)
    try:
        dateobject.strftime(outputformat)
    except (TypeError, ValueError) as err:
        LOGGER.error("wrong output format or type: %s %s", outputformat, err)
        return False
    # a format without any directive cannot produce a date
    if "%" not in outputformat:
        LOGGER.error("malformed output format: %s", outputformat)
        return False
    return True


def correct_year(year: int) -> int:
    """Adapt year from YY to YYYY format"""
    if year < 100:
        year += 1900 if year >= 90 else 2000
    return year


def plausible_year_filter(
    htmlstring: str,
    *,
    pattern: re.Pattern[str],
    yearpat: re.Pattern[str],
    earliest: datetime,
    latest: datetime,
) -> Counter[str]:
    """Filter the date patterns to find plausible years only"""
    occurrences = Counter(pattern.findall(htmlstring))  # slow!
    min_year, max_year = earliest.year, latest.year

    for item in list(occurrences):  # prevent RuntimeError
        year_match = yearpat.search(item)
        if year_match is None:
            LOGGER.debug("not a year pattern: %s", item)
            del occurrences[item]
            continue

        # correct_year() is a no-op on 4-digit years, so this covers both cases
        potential_year = correct_year(int(year_match[1]))

        if not min_year <= potential_year <= max_year:
            LOGGER.debug("no potential year: %s", item)
            del occurrences[item]

    return occurrences


def pick(dates: Iterable[datetime | None], options: Extractor) -> datetime | None:
    "Oldest date if original, else newest, by wall clock as written on the page."
    found = [d for d in dates if d is not None]
    if not found:
        return None
    best = (min if options.original else max)(
        found, key=lambda d: d.replace(tzinfo=None)
    )
    return validate(best, options.min, options.max)


def check_date_input(date_object: datetime | str | None, default: datetime) -> datetime:
    "Check if the input is a usable datetime or ISO date string, return default otherwise"
    if isinstance(date_object, datetime):
        return date_object
    if isinstance(date_object, str):
        try:
            return datetime.fromisoformat(date_object)
        except ValueError:
            LOGGER.warning("invalid datetime string: %s", date_object)
    return default  # no input or error thrown


def get_min_date(min_date: datetime | str | None) -> datetime:
    """Validates the minimum date and/or defaults to earliest plausible date"""
    return check_date_input(min_date, MIN_DATE)


def get_max_date(max_date: datetime | str | None) -> datetime:
    """Validates the maximum date and/or defaults to the end of the current day.
    A day-granular default stays stable across calls (unlike datetime.now()),
    which lets the date-validation caches be reused from one document to the
    next in batch processing, and accepts dates published earlier the same day."""
    end_of_today = datetime.now().replace(
        hour=23, minute=59, second=59, microsecond=999999
    )
    return check_date_input(max_date, end_of_today)

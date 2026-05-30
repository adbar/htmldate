# pylint:disable-msg=E0611,I1101
"""
Filters for date parsing and date validators.
"""

import logging
import re

from collections import Counter
from datetime import datetime
from functools import lru_cache

from .settings import CACHE_SIZE, MIN_DATE
from .utils import Extractor

LOGGER = logging.getLogger(__name__)
LOGGER.debug("minimum date setting: %s", MIN_DATE)


@lru_cache(maxsize=CACHE_SIZE)
def is_valid_date(
    date_input: datetime | str | None,
    outputformat: str,
    earliest: datetime,
    latest: datetime,
) -> bool:
    """Validate a string w.r.t. the chosen outputformat and basic heuristics"""
    # safety check
    if date_input is None:
        return False

    # try if date can be parsed using chosen outputformat
    if isinstance(date_input, datetime):
        dateobject = date_input
    else:
        # speed-up
        try:
            if outputformat == "%Y-%m-%d":
                dateobject = datetime(
                    int(date_input[:4]), int(date_input[5:7]), int(date_input[8:10])
                )
            # default
            else:
                dateobject = datetime.strptime(date_input, outputformat)
        except ValueError:
            return False

    # year first, then full validation: not newer than today or stored variable
    if (
        earliest.year <= dateobject.year <= latest.year
        and earliest.timestamp() <= dateobject.timestamp() <= latest.timestamp()
    ):
        return True
    LOGGER.debug("date not valid: %s", date_input)
    return False


def validate_and_convert(
    date_input: datetime | None,
    outputformat: str,
    earliest: datetime,
    latest: datetime,
) -> str | None:
    "Robust validation and conversion for plausible dates."
    if date_input is not None and is_valid_date(
        date_input, outputformat, earliest, latest
    ):
        try:
            LOGGER.debug("custom parse result: %s", date_input)
            return date_input.strftime(outputformat)
        except ValueError as err:  # pragma: no cover
            LOGGER.error("value error during conversion: %s %s", date_input, err)
    return None


@lru_cache(maxsize=16)
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


def plausible_year_filter(
    htmlstring: str,
    *,
    pattern: re.Pattern[str],
    yearpat: re.Pattern[str],
    earliest: datetime,
    latest: datetime,
    incomplete: bool = False,
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

        lastdigits = year_match[1]
        if not incomplete:
            potential_year = int(lastdigits)
        else:
            century = "19" if lastdigits[0] == "9" else "20"
            potential_year = int(century + lastdigits)

        if not min_year <= potential_year <= max_year:
            LOGGER.debug("no potential year: %s", item)
            del occurrences[item]

    return occurrences


def compare_values(reference: int, attempt: str, options: Extractor) -> int:
    """Compare the date expression to a reference"""
    try:
        timestamp = int(datetime.strptime(attempt, options.format).timestamp())
    except Exception as err:
        LOGGER.debug("datetime.strptime exception: %s for string %s", err, attempt)
        return reference
    if options.original:
        reference = min(reference, timestamp) if reference else timestamp
    else:
        reference = max(reference, timestamp)
    return reference


@lru_cache(maxsize=CACHE_SIZE)
def filter_ymd_candidate(
    bestmatch: re.Match[str],
    pattern: re.Pattern[str],
    copyear: int,
    outputformat: str,
    min_date: datetime,
    max_date: datetime,
) -> str | None:
    """Filter free text candidates in the YMD format"""
    if bestmatch is not None:
        pagedate = "-".join([bestmatch[1], bestmatch[2], bestmatch[3]])
        if is_valid_date(pagedate, "%Y-%m-%d", earliest=min_date, latest=max_date) and (
            copyear == 0 or int(bestmatch[1]) >= copyear
        ):
            LOGGER.debug('date found for pattern "%s": %s', pattern, pagedate)
            return convert_date(pagedate, "%Y-%m-%d", outputformat)
    return None


def convert_date(datestring: str, inputformat: str, outputformat: str) -> str:
    """Parse date and return string in desired format"""
    # speed-up (%Y-%m-%d)
    if inputformat == outputformat:
        return datestring
    # date object (speedup)
    if isinstance(datestring, datetime):
        return datestring.strftime(outputformat)
    # normal
    dateobject = datetime.strptime(datestring, inputformat)
    return dateobject.strftime(outputformat)


def check_extracted_reference(reference: int, options: Extractor) -> str | None:
    """Test if the extracted reference date can be returned"""
    if reference > 0:
        dateobject = datetime.fromtimestamp(reference)
        converted = dateobject.strftime(options.format)
        if is_valid_date(
            converted, options.format, earliest=options.min, latest=options.max
        ):
            return converted
    return None


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

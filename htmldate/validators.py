# pylint:disable-msg=E0611,I1101
"""
Filters for date parsing and date validators.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license

# standard
import logging

from collections import Counter
from datetime import datetime
from functools import lru_cache
from time import mktime
from typing import Match, Optional, Pattern, Union, Counter as Counter_Type

from .settings import CACHE_SIZE, MIN_DATE


LOGGER = logging.getLogger(__name__)
LOGGER.debug("minimum date setting: %s", MIN_DATE)


@lru_cache(maxsize=CACHE_SIZE)
def date_validator(
    date_input: Optional[Union[datetime, str]],
    outputformat: str,
    earliest: datetime,
    latest: datetime,
) -> bool:
    """Validate a string w.r.t. the chosen outputformat and basic heuristics"""
    # safety check
    if date_input is None:
        return False
    # try if date can be parsed using chosen outputformat
    if not isinstance(date_input, datetime):
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
    else:
        dateobject = date_input
    # basic year validation
    year = int(datetime.strftime(dateobject, "%Y"))
    min_year, max_year = earliest.year, latest.year
    # full validation: not newer than today or stored variable
    if (
        min_year <= year <= max_year
        and earliest.timestamp() <= dateobject.timestamp() <= latest.timestamp()
    ):
        return True
    LOGGER.debug("date not valid: %s", date_input)
    return False


@lru_cache(maxsize=16)
def output_format_validator(outputformat: str) -> bool:
    """Validate the output format in the settings"""
    # test with date object
    dateobject = datetime(2017, 9, 1, 0, 0)
    try:
        dateobject.strftime(outputformat)
    # other than ValueError: Python < 3.7 only
    except (NameError, TypeError, ValueError) as err:
        LOGGER.error("wrong output format or type: %s %s", outputformat, err)
        return False
    # test in abstracto
    if not isinstance(outputformat, str) or "%" not in outputformat:
        LOGGER.error("malformed output format: %s", outputformat)
        return False
    return True


def plausible_year_filter(
    htmlstring: str,
    *,
    pattern: Pattern[str],
    yearpat: Pattern[str],
    earliest: datetime,
    latest: datetime,
    incomplete: bool = False,
) -> Counter_Type[str]:
    """Filter the date patterns to find plausible years only"""
    # slow!
    occurrences = Counter(pattern.findall(htmlstring))
    toremove = set()
    # LOGGER.debug('occurrences: %s', occurrences)
    # look for implausible dates
    for item in occurrences.keys():
        # scrap implausible dates
        year_match = yearpat.search(item)
        if year_match is not None:
            if not incomplete:
                potential_year = int(year_match[1])
            else:
                lastdigits = year_match[1]
                if lastdigits[0] == "9":
                    potential_year = int("19" + lastdigits)
                else:
                    potential_year = int("20" + lastdigits)
            if not earliest.year <= potential_year <= latest.year:
                LOGGER.debug("no potential year: %s", item)
                toremove.add(item)
            # occurrences.remove(item)
            # continue
        else:
            LOGGER.debug("not a year pattern: %s", item)
            toremove.add(item)
    # remove candidates
    for item in toremove:
        del occurrences[item]
    return occurrences


def compare_values(
    reference: int, attempt: str, outputformat: str, original_date: bool
) -> int:
    """Compare the date expression to a reference"""
    try:
        timestamp = int(mktime(datetime.strptime(attempt, outputformat).timetuple()))
    except Exception as err:
        LOGGER.debug("datetime.strptime exception: %s for string %s", err, attempt)
        return reference
    if original_date and (reference == 0 or timestamp < reference):
        reference = timestamp
    elif not original_date and timestamp > reference:
        reference = timestamp
    return reference


@lru_cache(maxsize=CACHE_SIZE)
def filter_ymd_candidate(
    bestmatch: Match[str],
    pattern: Pattern[str],
    original_date: bool,
    copyear: int,
    outputformat: str,
    min_date: datetime,
    max_date: datetime,
) -> Optional[str]:
    """Filter free text candidates in the YMD format"""
    if bestmatch is not None:
        pagedate = "-".join([bestmatch[1], bestmatch[2], bestmatch[3]])
        if date_validator(
            pagedate, "%Y-%m-%d", earliest=min_date, latest=max_date
        ) is True and (copyear == 0 or int(bestmatch[1]) >= copyear):
            LOGGER.debug('date found for pattern "%s": %s', pattern, pagedate)
            return convert_date(pagedate, "%Y-%m-%d", outputformat)
            ## TODO: test and improve
            # if original_date is True:
            #    if copyear == 0 or int(bestmatch[1]) <= copyear:
            #        LOGGER.debug('date found for pattern "%s": %s', pattern, pagedate)
            #        return convert_date(pagedate, '%Y-%m-%d', outputformat)
            # else:
            #    if copyear == 0 or int(bestmatch[1]) >= copyear:
            #        LOGGER.debug('date found for pattern "%s": %s', pattern, pagedate)
            #        return convert_date(pagedate, '%Y-%m-%d', outputformat)
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


def check_extracted_reference(
    reference: int, outputformat: str, min_date: datetime, max_date: datetime
) -> Optional[str]:
    """Test if the extracted reference date can be returned"""
    if reference > 0:
        dateobject = datetime.fromtimestamp(reference)
        converted = dateobject.strftime(outputformat)
        if (
            date_validator(converted, outputformat, earliest=min_date, latest=max_date)
            is True
        ):
            return converted
    return None


def check_date_input(
    date_object: Optional[Union[datetime, str]], default: datetime
) -> datetime:
    "Check if the input is a usable datetime or ISO date string, return default otherwise"
    if isinstance(date_object, datetime):
        return date_object
    if isinstance(date_object, str):
        try:
            return datetime.fromisoformat(date_object)  # type: ignore
        except ValueError:
            LOGGER.warning("invalid datetime string: %s", date_object)
    return default  # no input or error thrown


def get_min_date(min_date: Optional[Union[datetime, str]]) -> datetime:
    """Validates the minimum date and/or defaults to earliest plausible date"""
    return check_date_input(min_date, MIN_DATE)


def get_max_date(max_date: Optional[Union[datetime, str]]) -> datetime:
    """Validates the maximum date and/or defaults to latest plausible date"""
    return check_date_input(max_date, datetime.now())

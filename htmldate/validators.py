# pylint:disable-msg=E0611,I1101
"""
Filters for date parsing and date validators.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license

# standard
import datetime
import logging
import time

from collections import Counter
from functools import lru_cache

from .settings import MIN_YEAR, LATEST_POSSIBLE, MAX_YEAR


LOGGER = logging.getLogger(__name__)
LOGGER.debug('date settings: %s %s %s', MIN_YEAR, LATEST_POSSIBLE, MAX_YEAR)


@lru_cache(maxsize=32)
def date_validator(date_input, outputformat, latest=LATEST_POSSIBLE):
    """Validate a string w.r.t. the chosen outputformat and basic heuristics"""
    # try if date can be parsed using chosen outputformat
    if not isinstance(date_input, datetime.date):
        # speed-up
        try:
            if outputformat == '%Y-%m-%d':
                dateobject = datetime.datetime(int(date_input[:4]),
                                               int(date_input[5:7]),
                                               int(date_input[8:10]))
            # default
            else:
                dateobject = datetime.datetime.strptime(date_input, outputformat)
        except ValueError:
            return False
    else:
        dateobject = date_input
    # basic year validation
    year = int(datetime.date.strftime(dateobject, '%Y'))
    if MIN_YEAR <= year <= MAX_YEAR:
        # not newer than today or stored variable
        try:
            if dateobject.date() <= latest:
                return True
        except AttributeError:
            if dateobject <= latest:
                return True
    LOGGER.debug('date not valid: %s', date_input)
    return False


def output_format_validator(outputformat):
    """Validate the output format in the settings"""
    # test in abstracto
    if not isinstance(outputformat, str) or not '%' in outputformat:
        logging.error('malformed output format: %s', outputformat)
        return False
    # test with date object
    dateobject = datetime.datetime(2017, 9, 1, 0, 0)
    try:
        dateobject.strftime(outputformat)
    except (NameError, TypeError, ValueError) as err:
        logging.error('wrong output format or format type: %s %s', outputformat, err)
        return False
    return True


@lru_cache(maxsize=32)
def plausible_year_filter(htmlstring, pattern, yearpat, tocomplete=False):
    """Filter the date patterns to find plausible years only"""
    # slow!
    allmatches = pattern.findall(htmlstring)
    occurrences = Counter(allmatches)
    toremove = set()
    # LOGGER.debug('occurrences: %s', occurrences)
    for item in occurrences.keys():
        # scrap implausible dates
        try:
            if tocomplete is False:
                potential_year = int(yearpat.search(item).group(1))
            else:
                lastdigits = yearpat.search(item).group(1)
                if lastdigits[0] == '9':
                    potential_year = int('19' + lastdigits)
                else:
                    potential_year = int('20' + lastdigits)
        except AttributeError:
            LOGGER.debug('not a year pattern: %s', item)
            toremove.add(item)
        else:
            if potential_year < MIN_YEAR or potential_year > MAX_YEAR:
                LOGGER.debug('no potential year: %s', item)
                toremove.add(item)
            # occurrences.remove(item)
            # continue
    # preventing dictionary changed size during iteration error
    for item in toremove:
        del occurrences[item]
    return occurrences


def compare_values(reference, attempt, outputformat, original_date):
    """Compare the date expression to a reference"""
    timestamp = time.mktime(datetime.datetime.strptime(attempt, outputformat).timetuple())
    if original_date is True:
        if reference == 0 or timestamp < reference:
            reference = timestamp
    else:
        if timestamp > reference:
            reference = timestamp
    return reference


@lru_cache(maxsize=32)
def filter_ymd_candidate(bestmatch, pattern, copyear, outputformat, max_date):
    """Filter free text candidates in the YMD format"""
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), bestmatch.group(3)])
        if date_validator(pagedate, '%Y-%m-%d', latest=max_date) is True:
            if copyear == 0 or int(bestmatch.group(1)) >= copyear:
                LOGGER.debug('date found for pattern "%s": %s', pattern, pagedate)
                return convert_date(pagedate, '%Y-%m-%d', outputformat)
    return None


def convert_date(datestring, inputformat, outputformat):
    """Parse date and return string in desired format"""
    # speed-up (%Y-%m-%d)
    if inputformat == outputformat:
        return str(datestring)
    # date object (speedup)
    if isinstance(datestring, datetime.date):
        return datestring.strftime(outputformat)
    # normal
    dateobject = datetime.datetime.strptime(datestring, inputformat)
    return dateobject.strftime(outputformat)


def check_extracted_reference(reference, outputformat, max_date):
    '''Test if the extracted reference date can be returned'''
    if reference > 0:
        dateobject = datetime.datetime.fromtimestamp(reference)
        converted = dateobject.strftime(outputformat)
        if date_validator(converted, outputformat, latest=max_date) is True:
            return converted
    return None


def get_max_date(max_date):
    '''Validates the maximum date and/or defaults to latest plausible date'''
    if max_date is not None:
        try:
            # internal conversion from Y-M-D format
            max_date = datetime.date(int(max_date[:4]),
                                     int(max_date[5:7]),
                                     int(max_date[8:10]))
        except ValueError:
            max_date = LATEST_POSSIBLE
    else:
        max_date = LATEST_POSSIBLE
    return max_date

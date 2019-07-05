# -*- coding: utf-8 -*-
# pylint:disable-msg=E0611,I1101
"""
Custom parsers for date extraction.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license

# standard
import datetime
import logging
import re

from .settings import PARSER
from .validators import convert_date, date_validator


## INIT
LOGGER = logging.getLogger(__name__)
# Regex cache
AMERICAN_ENGLISH = re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Januar|Jänner|Februar|Feber|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember) ([0-9]{1,2})(st|nd|rd|th)?,? ([0-9]{4})') # ([0-9]{2,4})
BRITISH_ENGLISH = re.compile(r'([0-9]{1,2})(st|nd|rd|th)? (of )?(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Januar|Jänner|Februar|Feber|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember),? ([0-9]{4})') # ([0-9]{2,4})
ENGLISH_DATE = re.compile(r'([0-9]{1,2})/([0-9]{1,2})/([0-9]{2,4})')
COMPLETE_URL = re.compile(r'([0-9]{4})[/-]([0-9]{1,2})[/-]([0-9]{1,2})')
PARTIAL_URL = re.compile(r'/([0-9]{4})/([0-9]{1,2})/')
YMD_PATTERN = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})')
DATESTUB_PATTERN = re.compile(r'([0-9]{1,2})\.([0-9]{1,2})\.([0-9]{2,4})')
GERMAN_TEXTSEARCH = re.compile(r'([0-9]{1,2})\. (Januar|Jänner|Februar|Feber|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember) ([0-9]{4})')
GENERAL_TEXTSEARCH = re.compile(r'January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Januar|Jänner|Februar|Feber|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember')
# German dates cache
TEXT_MONTHS = {'Januar':'01', 'Jänner':'01', 'January':'01', 'Jan':'01', 'Februar':'02', 'Feber':'02', 'February':'02', 'Feb':'02', 'März':'03', 'March':'03', 'Mar':'03', 'April':'04', 'Apr':'04', 'Mai':'05', 'May':'05', 'Juni':'06', 'June':'06', 'Jun':'06', 'Juli':'07', 'July':'07', 'Jul':'07', 'August':'08', 'Aug':'08', 'September':'09', 'Sep':'09', 'Oktober':'10', 'October':'10', 'Oct':'10', 'November':'11', 'Nov':'11', 'Dezember':'12', 'December':'12', 'Dec':'12'}


#@profile
def extract_url_date(testurl, outputformat):
    """Extract the date out of an URL string"""
    # easy extract in Y-M-D format
    match = COMPLETE_URL.search(testurl)
    if match:
        dateresult = match.group(0)
        LOGGER.debug('found date in URL: %s', dateresult)
        try:
            # converted = convert_date(dateresult, '%Y/%m/%d', outputformat)
            dateobject = datetime.datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            if date_validator(dateobject, outputformat) is True:
                converted = dateobject.strftime(outputformat)
                return converted
        except ValueError as err:
            LOGGER.debug('value error during conversion: %s %s', dateresult, err)
    # catchall
    return None


#@profile
def extract_partial_url_date(testurl, outputformat):
    """Extract an approximate date out of an URL string"""
    # easy extract in Y-M format
    match = PARTIAL_URL.search(testurl)
    if match:
        dateresult = match.group(0) + '/01'
        LOGGER.debug('found partial date in URL: %s', dateresult)
        try:
            # converted = convert_date(dateresult, '%Y/%m/%d', outputformat)
            dateobject = datetime.datetime(int(match.group(1)), int(match.group(2)), 1)
            if date_validator(dateobject, outputformat) is True:
                converted = dateobject.strftime(outputformat)
                return converted
        except ValueError as err:
            LOGGER.debug('value error during conversion: %s %s', dateresult, err)
    # catchall
    return None


#@profile
def regex_parse_de(string):
    """Try full-text parse for German date elements"""
    # text match
    match = GERMAN_TEXTSEARCH.search(string)
    if not match:
        return None
    # second element
    secondelem = TEXT_MONTHS[match.group(2)]
    # process and return
    try:
        dateobject = datetime.date(int(match.group(3)), int(secondelem), int(match.group(1)))
    except ValueError:
        return None
    LOGGER.debug('German text parse: %s', dateobject)
    return dateobject

#@profile
def regex_parse_en(string):
    """Try full-text parse for English date elements"""
    # https://github.com/vi3k6i5/flashtext ?
    # numbers
    match = ENGLISH_DATE.search(string)
    if match:
        day = match.group(2)
        month = match.group(1)
        year = match.group(3)
    else:
        # general search
        if not GENERAL_TEXTSEARCH.search(string):
            return None
        # American English
        match = AMERICAN_ENGLISH.search(string)
        if match:
            day = match.group(2)
            month = TEXT_MONTHS[match.group(1)]
            year = match.group(4)
        # British English
        else:
            match = BRITISH_ENGLISH.search(string)
            if match:
                day = match.group(1)
                month = TEXT_MONTHS[match.group(4)]
                year = match.group(5)
            else:
                return None
    # process and return
    if len(year) == 2:
        year = '20' + year
    try:
        dateobject = datetime.date(int(year), int(month), int(day))
    except ValueError:
        return None
    LOGGER.debug('English text parse: %s', dateobject)
    return dateobject


#@profile
def custom_parse(string, outputformat):
    """Try to bypass the slow dateparser"""
    LOGGER.debug('custom parse test: %s', string)
    # '201709011234' not covered by dateparser # regex was too slow
    if string[0:8].isdigit():
        try:
            candidate = datetime.date(int(string[:4]), int(string[4:6]), int(string[6:8]))
        except ValueError:
            return None
        if date_validator(candidate, '%Y-%m-%d') is True:
            LOGGER.debug('ymd match: %s', candidate)
            converted = convert_date(candidate, '%Y-%m-%d', outputformat)
            return converted
    # %Y-%m-%d search
    match = YMD_PATTERN.search(string)
    if match:
        try:
            candidate = datetime.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            LOGGER.debug('value error: %s', match.group(0))
        else:
            if date_validator(candidate, '%Y-%m-%d') is True:
                LOGGER.debug('ymd match: %s', candidate)
                converted = convert_date(candidate, '%Y-%m-%d', outputformat)
                return converted
    # faster than fire dateparser at once
    datestub = DATESTUB_PATTERN.search(string)
    if datestub and len(datestub.group(3)) in (2, 4):
        try:
            if len(datestub.group(3)) == 2:
                candidate = datetime.date(int('20' + datestub.group(3)), int(datestub.group(2)), int(datestub.group(1)))
            elif len(datestub.group(3)) == 4:
                candidate = datetime.date(int(datestub.group(3)), int(datestub.group(2)), int(datestub.group(1)))
        except ValueError:
            LOGGER.debug('value error: %s', datestub.group(0))
        else:
            # test candidate
            if date_validator(candidate, '%Y-%m-%d') is True:
                LOGGER.debug('D.M.Y match: %s', candidate)
                converted = convert_date(candidate, '%Y-%m-%d', outputformat)
                return converted
    # text match
    dateobject = regex_parse_de(string)
    if dateobject is None:
        dateobject = regex_parse_en(string)
    # examine
    if dateobject is not None:
        try:
            if date_validator(dateobject, outputformat) is True:
                LOGGER.debug('custom parse result: %s', dateobject)
                converted = dateobject.strftime(outputformat)
                return converted
        except ValueError as err:
            LOGGER.debug('value error during conversion: %s %s', string, err)
    return None


#@profile
def external_date_parser(string, outputformat, parser=PARSER):
    """Use the dateparser module"""
    LOGGER.debug('send to dateparser: %s', string)
    try:
        target = parser.get_date_data(string)['date_obj']
    # tzinfo.py line 323: loc_dt = dt + delta
    except OverflowError:
        target = None
    if target is not None:
        LOGGER.debug('dateparser result: %s', target)
        # datestring = datetime.date.strftime(target, outputformat)
        if date_validator(target, outputformat) is True:
            datestring = datetime.date.strftime(target, outputformat)
            return datestring
    return None

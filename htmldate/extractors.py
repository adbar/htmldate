# pylint:disable-msg=E0611,I1101
"""
Custom parsers and XPath expressions for date extraction
"""
## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license

# standard
import datetime
import logging
import re

from functools import lru_cache

# conditional imports with fallbacks for compatibility
# coverage for date parsing
try:
    import dateparser  # third-party, slow
    EXTERNAL_PARSER = dateparser.DateDataParser(settings={
        'PREFER_DAY_OF_MONTH': 'first', 'PREFER_DATES_FROM': 'past',
        'DATE_ORDER': 'DMY',
    })
    # allow_redetect_language=False, languages=['de', 'en'],
    EXTERNAL_PARSER_CONFIG = {
        'PREFER_DAY_OF_MONTH': 'first', 'PREFER_DATES_FROM': 'past',
        'DATE_ORDER': 'DMY'
    }
except ImportError:
    # try dateutil parser
    from dateutil.parser import parse as full_parse
    EXTERNAL_PARSER = None
    DEFAULT_PARSER_PARAMS = {'dayfirst': True, 'fuzzy': False}
else:
    full_parse = DEFAULT_PARSER_PARAMS = None
# iso date parsing speedup
try:
    from ciso8601 import parse_datetime, parse_datetime_as_naive
except ImportError:
    if not full_parse:
        from dateutil.parser import parse as full_parse
    parse_datetime = parse_datetime_as_naive = full_parse  # shortcut
# potential regex speedup
try:
    import regex
except ImportError:
    regex = re

# own
from .validators import convert_date, date_validator

LOGGER = logging.getLogger(__name__)

DATE_EXPRESSIONS = [
    """//*[contains(@id, 'date') or contains(@id, 'Date') or
    contains(@id, 'datum') or contains(@id, 'Datum') or contains(@id, 'time')
    or contains(@class, 'post-meta-time')]""",
    """//*[contains(@class, 'date') or contains(@class, 'Date')
    or contains(@class, 'datum') or contains(@class, 'Datum')]""",
    """//*[contains(@class, 'postmeta') or contains(@class, 'post-meta')
    or contains(@class, 'entry-meta') or contains(@class, 'postMeta')
    or contains(@class, 'post_meta') or contains(@class, 'post__meta') or
    contains(@class, 'article__date') or contains(@class, 'post_detail')]""",
    """//*[@class='meta' or @class='meta-before' or @class='asset-meta' or
    contains(@id, 'article-metadata') or contains(@class, 'article-metadata')
    or contains(@class, 'byline') or contains(@class, 'subline')]""",
    """//*[contains(@class, 'published') or contains(@class, 'posted') or
    contains(@class, 'submitted') or contains(@class, 'created-post')]""",
    """//*[contains(@id, 'lastmod') or contains(@itemprop, 'date') or
    contains(@class, 'time')]""",
    "//footer",
    "//*[@class='post-footer' or @class='footer' or @id='footer']",
    "//small",
    """//*[contains(@class, 'author') or contains(@class, 'autor') or
    contains(@class, 'field-content') or @class='meta' or
    contains(@class, 'info') or contains(@class, 'fa-clock-o') or
    contains(@class, 'publication')]""",
]

# supply more expressions for more languages
ADDITIONAL_EXPRESSIONS = [
    "//*[contains(@class, 'fecha') or contains(@class, 'parution')]",
]

# discard parts of the webpage
DISCARD_EXPRESSIONS = [
    './/footer',
    './/*[(self::div or self::section)][@id="footer" or @class="footer"]',
]

# Regex cache
AMERICAN_ENGLISH = re.compile(r'''(January|February|March|April|May|June|July|
August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|
Nov|Dec|Januar|Jänner|Februar|Feber|März|April|Mai|Juni|Juli|August|September|
Oktober|November|Dezember) ([0-9]{1,2})(st|nd|rd|th)?,? ([0-9]{4})''')
BRITISH_ENGLISH = re.compile(r'''([0-9]{1,2})(st|nd|rd|th)? (of )?(January|
February|March|April|May|June|July|August|September|October|November|December|
Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Januar|Jänner|Februar|Feber|
März|April|Mai|Juni|Juli|August|September|Oktober|November|
Dezember),? ([0-9]{4})''')
ENGLISH_DATE = re.compile(r'([0-9]{1,2})/([0-9]{1,2})/([0-9]{2,4})')
COMPLETE_URL = re.compile(r'([0-9]{4})[/-]([0-9]{1,2})[/-]([0-9]{1,2})')
PARTIAL_URL = re.compile(r'/([0-9]{4})/([0-9]{1,2})/')
YMD_PATTERN = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})')
DATESTUB_PATTERN = re.compile(r'([0-9]{1,2})\.([0-9]{1,2})\.([0-9]{2,4})')
GERMAN_TEXTSEARCH = re.compile(r'''([0-9]{1,2})\. (Januar|Jänner|Februar|
Feber|März|April|Mai|Juni|Juli|August|September|Oktober|
November|Dezember) ([0-9]{4})''')
GENERAL_TEXTSEARCH = re.compile(r'''January|February|March|April|May|June|July|
August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|
Nov|Dec|Januar|Jänner|Februar|Feber|März|April|Mai|Juni|Juli|August|September|
Oktober|November|Dezember''')
JSON_PATTERN = \
  re.compile(r'"date(?:Modified|Published)":"([0-9]{4}-[0-9]{2}-[0-9]{2})')
# use of regex module for speed
GERMAN_PATTERN = \
  regex.compile(r'(?:Datum|Stand): ?([0-9]{1,2})\.([0-9]{1,2})\.([0-9]{2,4})')
TIMESTAMP_PATTERN = regex.compile(r'([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{2}\.[0-9]{2}\.[0-9]{4}).[0-9]{2}:[0-9]{2}:[0-9]{2}')

# English + German dates cache
TEXT_MONTHS = {'Januar': '01', 'Jänner': '01', 'January': '01', 'Jan': '01',
               'Februar': '02', 'Feber': '02', 'February': '02', 'Feb': '02',
               'März': '03', 'March': '03', 'Mar': '03',
               'April': '04', 'Apr': '04',
               'Mai': '05', 'May': '05',
               'Juni': '06', 'June': '06', 'Jun': '06',
               'Juli': '07', 'July': '07', 'Jul': '07',
               'August': '08', 'Aug': '08',
               'September': '09', 'Sep': '09',
               'Oktober': '10', 'October': '10', 'Oct': '10',
               'November': '11', 'Nov': '11',
               'Dezember': '12', 'December': '12', 'Dec': '12'}

TEXT_DATE_PATTERN = re.compile(r'[.:,_/ -]|^[0-9]+$')
NO_TEXT_DATE_PATTERN = re.compile(r'[0-9]{2}:[0-9]{2}(:| )|\D*[0-9]{4}\D*$')


def discard_unwanted(tree):
    '''Delete unwanted sections of an HTML document and return them as a list'''
    my_discarded = []
    for expr in DISCARD_EXPRESSIONS:
        for subtree in tree.xpath(expr):
            my_discarded.append(subtree)
            subtree.getparent().remove(subtree)
    return tree, my_discarded


def extract_url_date(testurl, outputformat):
    """Extract the date out of an URL string complying with the Y-M-D format"""
    match = COMPLETE_URL.search(testurl)
    if match:
        dateresult = match.group(0)
        LOGGER.debug('found date in URL: %s', dateresult)
        try:
            dateobject = datetime.datetime(int(match.group(1)),
                                           int(match.group(2)),
                                           int(match.group(3)))
            if date_validator(dateobject, outputformat) is True:
                return dateobject.strftime(outputformat)
        except ValueError as err:
            LOGGER.debug('conversion error: %s %s', dateresult, err)
    return None


def extract_partial_url_date(testurl, outputformat):
    """Extract an approximate date out of an URL string in Y-M format"""
    match = PARTIAL_URL.search(testurl)
    if match:
        dateresult = match.group(0) + '/01'
        LOGGER.debug('found partial date in URL: %s', dateresult)
        try:
            dateobject = datetime.datetime(int(match.group(1)),
                                           int(match.group(2)),
                                           1)
            if date_validator(dateobject, outputformat) is True:
                return dateobject.strftime(outputformat)
        except ValueError as err:
            LOGGER.debug('conversion error: %s %s', dateresult, err)
    return None


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
        dateobject = datetime.date(int(match.group(3)),
                                   int(secondelem),
                                   int(match.group(1)))
    except ValueError:
        return None
    LOGGER.debug('German text parse: %s', dateobject)
    return dateobject


def regex_parse_en(string):
    """Try full-text parse for English date elements"""
    # https://github.com/vi3k6i5/flashtext ?
    # numbers
    match = ENGLISH_DATE.search(string)
    if match:
        day, month, year = match.group(2), match.group(1), match.group(3)
    else:
        # general search
        if not GENERAL_TEXTSEARCH.search(string):
            return None
        # American English
        match = AMERICAN_ENGLISH.search(string)
        if match:
            day, month, year = match.group(2), TEXT_MONTHS[match.group(1)], \
                               match.group(4)
        # British English
        else:
            match = BRITISH_ENGLISH.search(string)
            if match:
                day, month, year = match.group(1), TEXT_MONTHS[match.group(4)], \
                                   match.group(5)
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


def custom_parse(string, outputformat, extensive_search, max_date):
    """Try to bypass the slow dateparser"""
    LOGGER.debug('custom parse test: %s', string)
    # '201709011234' not covered by dateparser # regex was too slow
    if string[0:8].isdigit():
        try:
            candidate = datetime.date(int(string[:4]),
                                      int(string[4:6]),
                                      int(string[6:8]))
        except ValueError:
            return None
        if date_validator(candidate, '%Y-%m-%d') is True:
            LOGGER.debug('ymd match: %s', candidate)
            return convert_date(candidate, '%Y-%m-%d', outputformat)
    # much faster
    if string[0:4].isdigit():
        # try speedup with ciso8601 (if installed)
        try:
            if extensive_search is True:
                result = parse_datetime(string)
            # speed-up by ignoring time zone info if ciso8601 is installed
            else:
                result = parse_datetime_as_naive(string)
            if date_validator(result, outputformat, latest=max_date) is True:
                LOGGER.debug('parsing result: %s', result)
                return result.strftime(outputformat)
        except ValueError:
            LOGGER.debug('parsing error: %s', string)
    # %Y-%m-%d search
    match = YMD_PATTERN.search(string)
    if match:
        try:
            candidate = datetime.date(int(match.group(1)),
                                      int(match.group(2)),
                                      int(match.group(3)))
        except ValueError:
            LOGGER.debug('value error: %s', match.group(0))
        else:
            if date_validator(candidate, '%Y-%m-%d') is True:
                LOGGER.debug('ymd match: %s', candidate)
                return convert_date(candidate, '%Y-%m-%d', outputformat)
    # faster than fire dateparser at once
    datestub = DATESTUB_PATTERN.search(string)
    if datestub and len(datestub.group(3)) in (2, 4):
        try:
            if len(datestub.group(3)) == 2:
                candidate = datetime.date(int('20' + datestub.group(3)),
                                          int(datestub.group(2)),
                                          int(datestub.group(1)))
            elif len(datestub.group(3)) == 4:
                candidate = datetime.date(int(datestub.group(3)),
                                          int(datestub.group(2)),
                                          int(datestub.group(1)))
        except ValueError:
            LOGGER.debug('value error: %s', datestub.group(0))
        else:
            # test candidate
            if date_validator(candidate, '%Y-%m-%d') is True:
                LOGGER.debug('D.M.Y match: %s', candidate)
                return convert_date(candidate, '%Y-%m-%d', outputformat)
    # text match
    dateobject = regex_parse_de(string)
    if dateobject is None:
        dateobject = regex_parse_en(string)
    # copyright match?
    # © Janssen-Cilag GmbH 2014-2019. https://www.krebsratgeber.de/artikel/was-macht-eine-zelle-zur-krebszelle
    # examine
    if dateobject is not None:
        try:
            if date_validator(dateobject, outputformat) is True:
                LOGGER.debug('custom parse result: %s', dateobject)
                return dateobject.strftime(outputformat)
        except ValueError as err:
            LOGGER.debug('value error during conversion: %s %s', string, err)
    return None


def external_date_parser(string, outputformat):
    """Use dateutil parser or dateparser module according to system settings"""
    LOGGER.debug('send to external parser: %s', string)
    try:
        # dateparser installed or not
        if EXTERNAL_PARSER is not None:
            target = EXTERNAL_PARSER.get_date_data(string)['date_obj']
        else:
            target = full_parse(string, **DEFAULT_PARSER_PARAMS)
    # 2 types of errors possible
    except (OverflowError, ValueError):
        target = None
    # issue with data type
    if target is not None:
        return datetime.date.strftime(target, outputformat)
    return None


@lru_cache(maxsize=32)
def try_ymd_date(string, outputformat, extensive_search, max_date):
    """Use a series of heuristics and rules to parse a potential date expression"""
    # discard on formal criteria
    # list(filter(str.isdigit, string))
    if not string or len(string) < 6 or len([c for c in string if c.isdigit()]) < 4 \
    or not TEXT_DATE_PATTERN.search(string):
        return None
    # just time/single year, not a date
    if NO_TEXT_DATE_PATTERN.match(string):
        return None
    # faster
    customresult = custom_parse(string, outputformat, extensive_search, max_date)
    if customresult is not None:
        return customresult
    # slow but extensive search
    if extensive_search is True:
        # send to date parser
        dateparser_result = external_date_parser(string, outputformat)
        if dateparser_result is not None:
            if date_validator(dateparser_result, outputformat, latest=max_date):
                return dateparser_result
    return None


def json_search(htmlstring, outputformat, max_date):
    '''Look for JSON time patterns throughout the web page'''
    json_match = JSON_PATTERN.search(htmlstring)
    if json_match and date_validator(json_match.group(1), '%Y-%m-%d', latest=max_date):
        LOGGER.debug('JSON time found: %s', json_match.group(0))
        return convert_date(json_match.group(1), '%Y-%m-%d', outputformat)
    return None


def timestamp_search(htmlstring, outputformat, max_date):
    '''Look for timestamps throughout the web page'''
    tstamp_match = TIMESTAMP_PATTERN.search(htmlstring)
    if tstamp_match and date_validator(tstamp_match.group(1), '%Y-%m-%d', latest=max_date):
        LOGGER.debug('time regex found: %s', tstamp_match.group(0))
        return convert_date(tstamp_match.group(1), '%Y-%m-%d', outputformat)
    return None


def german_text_search(htmlstring, outputformat, max_date):
    '''Look for precise German patterns throughout the web page'''
    de_match = GERMAN_PATTERN.search(htmlstring)
    if de_match and len(de_match.group(3)) in (2, 4):
        try:
            if len(de_match.group(3)) == 2:
                candidate = datetime.date(int('20' + de_match.group(3)),
                                          int(de_match.group(2)),
                                          int(de_match.group(1)))
            else:
                candidate = datetime.date(int(de_match.group(3)),
                                          int(de_match.group(2)),
                                          int(de_match.group(1)))
        except ValueError:
            LOGGER.debug('value error: %s', de_match.group(0))
        else:
            if date_validator(candidate, '%Y-%m-%d', latest=max_date) is True:
                LOGGER.debug('precise pattern found: %s', de_match.group(0))
                return convert_date(candidate, '%Y-%m-%d', outputformat)
    return None

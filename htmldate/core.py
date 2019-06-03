# -*- coding: utf-8 -*-
"""
Module bundling all functions needed to determine the date of HTML strings or LXML trees.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license


# standard
import datetime
import logging
import re
import time

from collections import Counter
from io import StringIO # Python 3

# third-party
import ciso8601
import dateparser
from lxml import etree, html
from lxml.html.clean import Cleaner
import regex

# own
from .download import fetch_url
# import settings


## TODO:
# manually set latestdate, latestdate != TODAY
# from og:image or <img>?
# MODIFIED vs CREATION date switch?
# .lower() in tags and attributes?
# time-ago datetime= relative-time datetime=
# German/English switch


## INIT
logger = logging.getLogger(__name__)

DATE_EXPRESSIONS = [
    "//*[contains(@class, 'date') or contains(@class, 'Date') or contains(@class, 'datum') or contains(@class, 'Datum')]",
    "//*[contains(@id, 'date') or contains(@id, 'Date') or contains(@id, 'datum') or contains(@id, 'Datum')]",
    "//*[contains(@class, 'time') or contains(@id, 'time')]",
    "//*[contains(@class, 'byline') or contains(@class, 'subline') or contains(@class, 'info')]",
    "//*[contains(@class, 'postmeta') or contains(@class, 'post-meta') or contains(@class, 'entry-meta') or contains(@class, 'postMeta') or contains(@class, 'post_meta') or contains(@class, 'post__meta')]",
    "//*[@class='meta' or @class='meta-before' or @class='asset-meta']",
    "//*[contains(@class, 'published') or contains(@class, 'posted') or contains(@class, 'submitted') or contains(@class, 'created-post')]",
    "//*[contains(@id, 'lastmod')]",
    "//*[contains(@itemprop, 'date')]",
    "//footer",
    "//*[@class='post-footer']",
    "//*[@class='footer' or @id='footer']",
    "//small",
    "//*[contains(@class, 'author') or contains(@class, 'field-content')]",
]
# "//*[contains(@class, 'fa-clock-o')]",
# "//*[contains(@id, 'metadata')]",

## Plausible dates
# earliest possible year to take into account (inclusive)
MIN_YEAR = 1995
# latest possible date
TODAY = datetime.date.today()
# latest possible year
MAX_YEAR = datetime.date.today().year

## DateDataParser object
PARSERCONFIG = {'PREFER_DAY_OF_MONTH': 'first', 'PREFER_DATES_FROM': 'past', 'DATE_ORDER': 'DMY'}

logger.debug('settings: %s %s %s', MIN_YEAR, TODAY, MAX_YEAR)
logger.debug('dateparser configuration: %s', PARSERCONFIG)

# LXML
HTML_PARSER = html.HTMLParser() # encoding='utf8'

cleaner = Cleaner()
cleaner.comments = False
cleaner.embedded = True
cleaner.forms = False
cleaner.frames = True
cleaner.javascript = True
cleaner.links = False
cleaner.meta = False
cleaner.page_structure = True
cleaner.processing_instructions = True
cleaner.remove_unknown_tags = False
cleaner.safe_attrs_only = False
cleaner.scripts = False
cleaner.style = True
cleaner.kill_tags = ['audio', 'canvas', 'label', 'map', 'math', 'object', 'picture', 'rdf', 'svg', 'video'] # 'embed', 'figure', 'img', 'table'

TEXT_MONTHS = {'Januar':'01', 'Jänner':'01', 'January':'01', 'Jan':'01', 'Februar':'02', 'Feber':'02', 'February':'02', 'Feb':'02', 'März':'03', 'March':'03', 'Mar':'03', 'April':'04', 'Apr':'04', 'Mai':'05', 'May':'05', 'Juni':'06', 'June':'06', 'Jun':'06', 'Juli':'07', 'July':'07', 'Jul':'07', 'August':'08', 'Aug':'08', 'September':'09', 'Sep':'09', 'Oktober':'10', 'October':'10', 'Oct':'10', 'November':'11', 'Nov':'11', 'Dezember':'12', 'December':'12', 'Dec':'12'}

## REGEX cache
american_english = re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Januar|Jänner|Februar|Feber|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember) ([0-9]{1,2})(st|nd|rd|th)?,? ([0-9]{4})') # ([0-9]{2,4})
british_english = re.compile(r'([0-9]{1,2})(st|nd|rd|th)? (of )?(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Januar|Jänner|Februar|Feber|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember),? ([0-9]{4})') # ([0-9]{2,4})
english_date = re.compile(r'([0-9]{1,2})/([0-9]{1,2})/([0-9]{2,4})')
general_textsearch = re.compile(r'January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Januar|Jänner|Februar|Feber|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember')
german_textsearch = re.compile(r'([0-9]{1,2})\. (Januar|Jänner|Februar|Feber|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember) ([0-9]{4})')
complete_url = re.compile(r'([0-9]{4})/([0-9]{2})/([0-9]{2})')
partial_url = re.compile(r'/([0-9]{4})/([0-9]{2})/')
ymd_pattern = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})')
datestub_pattern = re.compile(r'([0-9]{1,2})\.([0-9]{1,2})\.([0-9]{2,4})')
json_pattern = re.compile(r'"date(?:Modified|Published)":"([0-9]{4}-[0-9]{2}-[0-9]{2})')
# use of regex module for speed
german_pattern = regex.compile(r'(?:Datum|Stand): ?([0-9]{1,2})\.([0-9]{1,2})\.([0-9]{2,4})')
timestamp_pattern = regex.compile(r'([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{2}\.[0-9]{2}\.[0-9]{4}).[0-9]{2}:[0-9]{2}:[0-9]{2}')


#@profile
def date_validator(date_input, outputformat):
    """Validate a string with respect to the chosen outputformat and basic heuristics"""
    # try if date can be parsed using chosen outputformat
    if not isinstance(date_input, datetime.date):
        # speed-up
        try:
            if outputformat == '%Y-%m-%d':
                dateobject = datetime.datetime(int(date_input[:4]), int(date_input[5:7]), int(date_input[8:10]))
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
        # not newer than today
        try:
            if dateobject.date() <= TODAY:
                return True
        except AttributeError:
            if dateobject <= TODAY:
                return True
    logger.debug('date not valid: %s', date_input)
    return False


#@profile
def output_format_validator(outputformat):
    """Validate the output format in the settings"""
    # test in abstracto
    if not isinstance(outputformat, str) or not '%' in outputformat:
        logging.error('malformed output format: %s', outputformat)
        return False
    # test with date object
    dateobject = datetime.datetime(2017, 9, 1, 0, 0)
    try:
        # datetime.datetime.strftime(dateobject, outputformat)
        dateobject.strftime(outputformat)
    except (NameError, TypeError, ValueError) as err:
        logging.error('wrong output format or format type: %s %s', outputformat, err)
        return False
    return True


#@profile
def convert_date(datestring, inputformat, outputformat):
    """Parse date and return string in desired format"""
    # speed-up (%Y-%m-%d)
    if inputformat == outputformat:
        return str(datestring)
    # date object (speedup)
    if isinstance(datestring, datetime.date):
        converted = datestring.strftime(outputformat)
        return converted
    # normal
    dateobject = datetime.datetime.strptime(datestring, inputformat)
    converted = dateobject.strftime(outputformat)
    return converted


#@profile
def regex_parse_de(string):
    """Try full-text parse for German date elements"""
    # text match
    match = german_textsearch.search(string)
    if not match:
        return None
    # second element
    secondelem = TEXT_MONTHS[match.group(2)]
    # process and return
    try:
        dateobject = datetime.date(int(match.group(3)), int(secondelem), int(match.group(1)))
    except ValueError:
        return None
    logger.debug('German text parse: %s', dateobject)
    return dateobject

#@profile
def regex_parse_en(string):
    """Try full-text parse for English date elements"""
    # https://github.com/vi3k6i5/flashtext ?
    # numbers
    match = english_date.search(string)
    if match:
        day = match.group(2)
        month = match.group(1)
        year = match.group(3)
    else:
        # general search
        if not general_textsearch.search(string):
            return None
        # American English
        match = american_english.search(string)
        if match:
            day = match.group(2)
            month = TEXT_MONTHS[match.group(1)]
            year = match.group(4)
        # British English
        else:
            match = british_english.search(string)
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
    logger.debug('English text parse: %s', dateobject)
    return dateobject


#@profile
def custom_parse(string, outputformat):
    """Try to bypass the slow dateparser"""
    logger.debug('custom parse test: %s', string)
    # '201709011234' not covered by dateparser # regex was too slow
    if string[0:8].isdigit():
        try:
            candidate = datetime.date(int(string[:4]), int(string[4:6]), int(string[6:8]))
        except ValueError:
            return None
        if date_validator(candidate, '%Y-%m-%d') is True:
            logger.debug('ymd match: %s', candidate)
            converted = convert_date(candidate, '%Y-%m-%d', outputformat)
            return converted
    # %Y-%m-%d search
    match = ymd_pattern.search(string)
    if match:
        try:
            candidate = datetime.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            logger.debug('value error: %s', match.group(0))
        else:
            if date_validator(candidate, '%Y-%m-%d') is True:
                logger.debug('ymd match: %s', candidate)
                converted = convert_date(candidate, '%Y-%m-%d', outputformat)
                return converted
    # faster than fire dateparser at once
    datestub = datestub_pattern.search(string)
    if datestub and len(datestub.group(3)) in (2, 4):
        try:
            if len(datestub.group(3)) == 2:
                candidate = datetime.date(int('20' + datestub.group(3)), int(datestub.group(2)), int(datestub.group(1)))
            elif len(datestub.group(3)) == 4:
                candidate = datetime.date(int(datestub.group(3)), int(datestub.group(2)), int(datestub.group(1)))
        except ValueError:
            logger.debug('value error: %s', datestub.group(0))
        else:
            # test candidate
            if date_validator(candidate, '%Y-%m-%d') is True:
                logger.debug('D.M.Y match: %s', candidate)
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
                logger.debug('custom parse result: %s', dateobject)
                converted = dateobject.strftime(outputformat)
                return converted
        except ValueError as err:
            logger.debug('value error during conversion: %s %s', string, err)
    return None


#@profile
def external_date_parser(string, outputformat, parser=dateparser.DateDataParser(settings=PARSERCONFIG)):
    """Use the dateparser module"""
    logger.debug('send to dateparser: %s', string)
    try:
        target = parser.get_date_data(string)['date_obj']
    # tzinfo.py line 323: loc_dt = dt + delta
    except OverflowError:
        target = None
    if target is not None:
        logger.debug('dateparser result: %s', target)
        # datestring = datetime.date.strftime(target, outputformat)
        if date_validator(target, outputformat) is True:
            datestring = datetime.date.strftime(target, outputformat)
            return datestring
    return None


#@profile
def try_ymd_date(string, outputformat, parser=dateparser.DateDataParser(settings=PARSERCONFIG)):
    """Use a series of heuristics and rules to parse a potential date expression"""
    # discard on formal criteria
    if string is None or len(list(filter(str.isdigit, string))) < 4:
        return None
    # just time/single year, not a date
    if re.match(r'[0-9]{2}:[0-9]{2}(:| )', string) or re.match(r'\D*[0-9]{4}\D*$', string):
        return None
    # much faster
    if string[0:4].isdigit():
        # try speedup with ciso8601
        try:
            result = ciso8601.parse_datetime_as_naive(string)
            if date_validator(result, outputformat) is True:
                logger.debug('ciso8601 result: %s', result)
                converted = result.strftime(outputformat)
                return converted
        except ValueError:
            logger.debug('ciso8601 error: %s', string)
    # faster
    customresult = custom_parse(string, outputformat)
    if customresult is not None:
        return customresult
    # slow but extensive search
    if find_date.extensive_search is True:
        # send to dateparser
        dateparser_result = external_date_parser(string, outputformat, parser)
        if dateparser_result is not None:
            return dateparser_result
    # catchall
    return None


#@profile
def compare_reference(reference, expression, outputformat):
    """Compare the date expression to a reference"""
    # trim
    temptext = expression.strip()
    temptext = re.sub(r'[\n\r\s\t]+', ' ', temptext, re.MULTILINE)
    textcontent = temptext.strip()
    # simple length heuristics
    if not textcontent or len(list(filter(str.isdigit, textcontent))) < 4:
        return reference
    # try the beginning of the string
    textcontent = textcontent[:48]
    attempt = try_ymd_date(textcontent, outputformat)
    if attempt is not None:
        timestamp = time.mktime(datetime.datetime.strptime(attempt, outputformat).timetuple())
        if timestamp > reference:
            return timestamp
        return reference
    # else:
    return reference


#@profile
def extract_url_date(testurl, outputformat):
    """Extract the date out of an URL string"""
    # easy extract in Y-M-D format
    match = complete_url.search(testurl)
    if match:
        dateresult = match.group(0)
        logger.debug('found date in URL: %s', dateresult)
        try:
            # converted = convert_date(dateresult, '%Y/%m/%d', outputformat)
            dateobject = datetime.datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            if date_validator(dateobject, outputformat) is True:
                converted = dateobject.strftime(outputformat)
                return converted
        except ValueError as err:
            logger.debug('value error during conversion: %s %s', dateresult, err)
    # test another pattern
    else:
        match = re.search(r'([0-9]{4})-([0-9]{2})-([0-9]{2})', testurl)
        if match:
            dateresult = match.group(0)
            logger.debug('found date in URL: %s', dateresult)
            try:
                # converted = convert_date(dateresult, '%Y-%m-%d', outputformat)
                dateobject = datetime.datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                if date_validator(dateobject, outputformat) is True:
                    converted = dateobject.strftime(outputformat)
                    return converted
            except ValueError as err:
                logger.debug('value error during conversion: %s %s', dateresult, err)
    # catchall
    return None


#@profile
def extract_partial_url_date(testurl, outputformat):
    """Extract an approximate date out of an URL string"""
    # easy extract in Y-M format
    match = partial_url.search(testurl)
    if match:
        dateresult = match.group(0) + '/01'
        logger.debug('found date in URL: %s', dateresult)
        try:
            # converted = convert_date(dateresult, '%Y/%m/%d', outputformat)
            dateobject = datetime.datetime(int(match.group(1)), int(match.group(2)), 1)
            if date_validator(dateobject, outputformat) is True:
                converted = dateobject.strftime(outputformat)
                return converted
        except ValueError as err:
            logger.debug('value error during conversion: %s %s', dateresult, err)
    # catchall
    return None


#@profile
def examine_date_elements(tree, expression, outputformat):
    """Check HTML elements one by one for date expressions"""
    try:
        elements = tree.xpath(expression)
    except etree.XPathEvalError as err:
        logger.error('lxml expression %s throws an error: %s', expression, err)
        return None
    if not elements: # is not None and len(elements) > 0
        return None
    # loop through the elements to analyze
    for elem in elements:
        # trim
        temptext = elem.text_content().strip()
        temptext = re.sub(r'[\n\r\s\t]+', ' ', temptext, re.MULTILINE)
        textcontent = temptext.strip()
        # simple length heuristics
        if not textcontent or len(textcontent) < 6:
            continue
        # try the beginning of the string
        else:
            # shorten
            toexamine = textcontent[:48]
            # trim non-digits at the end of the string
            toexamine = re.sub(r'\D+$', '', toexamine)
            #toexamine = re.sub(r'\|.+$', '', toexamine)
            # more than 4 digits required
            if len(toexamine) < 7 or len(list(filter(str.isdigit, toexamine))) < 4:
                continue
            logger.debug('analyzing (HTML): %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip()[:100])
            logger.debug('analyzing (string): %s', toexamine)
            attempt = try_ymd_date(toexamine, outputformat)
            if attempt is not None:
                return attempt
    # catchall
    return None


#@profile
def examine_header(tree, outputformat):
    """Parse header elements to find date cues"""
    headerdate = None
    reserve = None
    try:
        # loop through all meta elements
        for elem in tree.xpath('//meta'): # was //head/meta
            # safeguard
            if len(elem.attrib) < 1:
                continue
            # property attribute
            if 'property' in elem.attrib: # elem.get('property') is not None:
                # safeguard
                if elem.get('content') is None or len(elem.get('content')) < 1:
                    continue
                # "og:" for OpenGraph http://ogp.me/
                if elem.get('property').lower() in ('article:published_time', 'bt:pubdate', 'dc:created', 'dc:date', 'og:article:published_time', 'og:published_time', 'rnews:datepublished') and headerdate is None:
                    logger.debug('examining meta property: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    headerdate = try_ymd_date(elem.get('content'), outputformat)
                # modified: override published_time
                elif elem.get('property').lower() in ('article:modified_time', 'og:article:modified_time', 'og:updated_time'):
                    logger.debug('examining meta property: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    attempt = try_ymd_date(elem.get('content'), outputformat)
                    if attempt is not None:
                        headerdate = attempt
            # name attribute
            elif headerdate is None and 'name' in elem.attrib: # elem.get('name') is not None:
                # safeguard
                if elem.get('content') is None or len(elem.get('content')) < 1:
                    continue
                # url
                elif elem.get('name').lower() == 'og:url':
                    headerdate = extract_url_date(elem.get('content'), outputformat)
                # date
                elif elem.get('name').lower() in ('article.created', 'article_date_original', 'article.published', 'created', 'cxenseparse:recs:publishtime', 'date', 'date_published', 'dc.date', 'dc.date.created', 'dc.date.issued', 'dcterms.date', 'gentime', 'lastmodified', 'last-modified', 'og:published_time', 'originalpublicationdate', 'pubdate', 'publishdate', 'publish_date', 'published-date', 'publication_date', 'sailthru.date', 'timestamp'):
                    logger.debug('examining meta name: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    headerdate = try_ymd_date(elem.get('content'), outputformat)
            elif headerdate is None and 'pubdate' in elem.attrib:
                if elem.get('pubdate').lower() == 'pubdate':
                    logger.debug('examining meta pubdate: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    headerdate = try_ymd_date(elem.get('content'), outputformat)
            # other types # itemscope?
            elif headerdate is None and 'itemprop' in elem.attrib:
                if elem.get('itemprop').lower() in ('datecreated', 'datepublished', 'pubyear') and headerdate is None:
                    logger.debug('examining meta itemprop: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    if 'datetime' in elem.attrib:
                        headerdate = try_ymd_date(elem.get('datetime'), outputformat)
                    elif 'content' in elem.attrib:
                        headerdate = try_ymd_date(elem.get('content'), outputformat)
                # override
                elif elem.get('itemprop').lower() == 'datemodified':
                    logger.debug('examining meta itemprop: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    if 'datetime' in elem.attrib:
                        attempt = try_ymd_date(elem.get('datetime'), outputformat)
                    elif 'content' in elem.attrib:
                        attempt = try_ymd_date(elem.get('content'), outputformat)
                    if attempt is not None:
                        headerdate = attempt
                # reserve with copyrightyear
                elif headerdate is None and elem.get('itemprop').lower() == 'copyrightyear':
                    logger.debug('examining meta itemprop: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    if 'content' in elem.attrib:
                        attempt = '-'.join([elem.get('content'), '01', '01'])
                        if date_validator(attempt, '%Y-%m-%d') is True:
                            reserve = attempt
            # http-equiv, rare http://www.standardista.com/html5/http-equiv-the-meta-attribute-explained/
            elif headerdate is None and 'http-equiv' in elem.attrib:
                if elem.get('http-equiv').lower() in ('date', 'last-modified') and headerdate is None:
                    logger.debug('examining meta http-equiv: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    headerdate = try_ymd_date(elem.get('content'), outputformat)
            #else:
            #    logger.debug('not found: %s %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip(), elem.attrib)


        # if nothing was found, look for lower granularity (so far: "copyright year")
        if headerdate is None and reserve is not None:
            logger.debug('opting for reserve date with less granularity')
            headerdate = reserve

    except etree.XPathEvalError as err:
        logger.error('XPath %s', err)
        return None

    if headerdate is not None: # and date_validator(headerdate, outputformat) is True
        return headerdate
    return None


#@profile
def plausible_year_filter(htmlstring, pattern, yearpat, tocomplete=False):
    """Filter the date patterns to find plausible years only"""
    ## slow
    allmatches = pattern.findall(htmlstring)
    occurrences = Counter(allmatches)
    toremove = set()
    # logger.debug('occurrences: %s', occurrences)
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
            logger.debug('not a year pattern: %s', item)
            toremove.add(item)
        else:
            if potential_year < MIN_YEAR or potential_year > MAX_YEAR:
                logger.debug('no potential year: %s', item)
                toremove.add(item)
            # occurrences.remove(item)
            # continue
    # record
    for item in toremove:
        del occurrences[item]
    return occurrences


#@profile
def select_candidate(occurrences, catch, yearpat):
    """Select a candidate among the most frequent matches"""
    # logger.debug('occurrences: %s', occurrences)
    if len(occurrences) == 0:
        return None
    if len(occurrences) == 1:
        match = catch.search(list(occurrences.keys())[0])
        if match:
            return match
    # select among most frequent
    firstselect = occurrences.most_common(10)
    logger.debug('firstselect: %s', firstselect)
    # sort and find probable candidates
    bestones = sorted(firstselect, reverse=True)[:2]
    first_pattern = bestones[0][0]
    first_count = bestones[0][1]
    second_pattern = bestones[1][0]
    second_count = bestones[1][1]
    logger.debug('bestones: %s', bestones)
    # same number of occurrences: always take most recent
    if first_count == second_count:
        match = catch.search(first_pattern)
    else:
        year1 = int(yearpat.search(first_pattern).group(1))
        year2 = int(yearpat.search(second_pattern).group(1))
        # safety net: plausibility
        if date_validator(str(year1), '%Y') is False:
            if date_validator(str(year2), '%Y') is True:
                # logger.debug('first candidate not suitable: %s', year1)
                match = catch.match(second_pattern)
            else:
                logger.debug('no suitable candidate: %s %s', year1, year2)
                return None
        # safety net: newer date but up to 50% less frequent
        if year2 > year1 and second_count/first_count > 0.5:
            match = catch.match(second_pattern)
        # not newer or hopefully not significant
        else:
            match = catch.match(first_pattern)
    if match:
        return match
    return None


#@profile
def filter_ymd_candidate(bestmatch, pattern, copyear, outputformat):
    """Filter free text candidates in the YMD format"""
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), bestmatch.group(3)])
        if date_validator(pagedate, '%Y-%m-%d') is True:
            if copyear == 0 or int(bestmatch.group(1)) >= copyear:
                logger.debug('date found for pattern "%s": %s', pattern, pagedate)
                return convert_date(pagedate, '%Y-%m-%d', outputformat)
    return None


#@profile
def search_pattern(htmlstring, pattern, catch, yearpat):
    """Chained candidate filtering and selection"""
    candidates = plausible_year_filter(htmlstring, pattern, yearpat)
    return select_candidate(candidates, catch, yearpat)


#@profile
def search_page(htmlstring, outputformat):
    """Search the page for common patterns (can lead to flawed results!)"""
    # init
    # TODO: © Janssen-Cilag GmbH 2014-2019. https://www.krebsratgeber.de/artikel/was-macht-eine-zelle-zur-krebszelle
    # date ultimate rescue for the rest: most frequent year/month comination in the HTML

    # copyright symbol
    logger.debug('looking for copyright/footer information')
    copyear = 0
    pattern = re.compile(r'(?:©|&copy;|Copyright|\(c\))\D+([12][0-9]{3})\D')
    yearpat = re.compile(r'^\D?([12][0-9]{3})')
    catch = re.compile(r'^\D?([12][0-9]{3})')
    candidates = plausible_year_filter(htmlstring, pattern, yearpat)
    bestmatch = select_candidate(candidates, catch, yearpat)
    #bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        logger.debug('Copyright detected: %s', bestmatch.group(0))
        pagedate = '-'.join([bestmatch.group(0), '07', '01'])
        if date_validator(bestmatch.group(0), '%Y') is True:
            logger.debug('date found for copyright/footer pattern "%s": %s', pattern, pagedate)
            copyear = int(bestmatch.group(0))
            # return convert_date(pagedate, '%Y-%m-%d', outputformat)

    ## 3 components
    logger.debug('3 components')
    # target URL characteristics
    pattern = re.compile(r'/([0-9]{4}/[0-9]{2}/[0-9]{2})[01/]')
    yearpat = re.compile(r'^\D?([12][0-9]{3})')
    catch = re.compile(r'([0-9]{4})/([0-9]{2})/([0-9]{2})')
    candidates = plausible_year_filter(htmlstring, pattern, yearpat)
    bestmatch = select_candidate(candidates, catch, yearpat)
    # bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    result = filter_ymd_candidate(bestmatch, pattern, copyear, outputformat)
    if result is not None:
        return result

    # more loosely structured data
    pattern = re.compile(r'\D([0-9]{4}[/.-][0-9]{2}[/.-][0-9]{2})\D')
    yearpat = re.compile(r'^\D?([12][0-9]{3})')
    catch = re.compile(r'([0-9]{4})[/.-]([0-9]{2})[/.-]([0-9]{2})')
    candidates = plausible_year_filter(htmlstring, pattern, yearpat)
    bestmatch = select_candidate(candidates, catch, yearpat)
    # bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    result = filter_ymd_candidate(bestmatch, pattern, copyear, outputformat)
    if result is not None:
        return result

    #
    pattern = re.compile(r'\D([0-3]?[0-9][/.-][01]?[0-9][/.-][0-9]{4})\D')
    yearpat = re.compile(r'(19[0-9]{2}|20[0-9]{2})\D?$')
    candidates = plausible_year_filter(htmlstring, pattern, yearpat)
    # revert DD-MM-YYYY patterns before sorting
    replacement = dict()
    for item in candidates:
        match = re.match(r'([0-3]?[0-9])[/.-]([01]?[0-9])[/.-]([0-9]{4})', item)
        if len(match.group(1)) == 1:
            day = '0' + match.group(1)
        else:
            day = match.group(1)
        if len(match.group(2)) == 1:
            month = '0' + match.group(2)
        else:
            month = match.group(2)
        candidate = '-'.join([match.group(3), month, day])
        replacement[candidate] = candidates[item]
    candidates = Counter(replacement)
    catch = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})')
    yearpat = re.compile(r'^([0-9]{4})')
    # select
    bestmatch = select_candidate(candidates, catch, yearpat)
    result = filter_ymd_candidate(bestmatch, pattern, copyear, outputformat)
    if result is not None:
        return result

    # valid dates strings
    pattern = re.compile(r'(\D19[0-9]{2}[01][0-9][0-3][0-9]\D|\D20[0-9]{2}[01][0-9][0-3][0-9]\D)')
    yearpat = re.compile(r'^\D?([12][0-9]{3})')
    catch = re.compile(r'([12][0-9]{3})([01][0-9])([0-3][0-9])')
    candidates = plausible_year_filter(htmlstring, pattern, yearpat)
    bestmatch = select_candidate(candidates, catch, yearpat)
    # bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    result = filter_ymd_candidate(bestmatch, pattern, copyear, outputformat)
    if result is not None:
        return result

    # DD?/MM?/YY
    pattern = re.compile(r'\D([0-3]?[0-9][/.][01]?[0-9][/.][019][0-9])\D')
    yearpat = re.compile(r'([0-9]{2})$')
    candidates = plausible_year_filter(htmlstring, pattern, yearpat, tocomplete=True)
    # revert DD-MM-YYYY patterns before sorting
    replacement = dict()
    for item in candidates:
        match = re.match(r'([0-3]?[0-9])[/.]([01]?[0-9])[/.]([0-9]{2})', item)
        if len(match.group(1)) == 1:
            day = '0' + match.group(1)
        else:
            day = match.group(1)
        if len(match.group(2)) == 1:
            month = '0' + match.group(2)
        else:
            month = match.group(2)
        if match.group(3)[0] == '9':
            year = '19' + match.group(3)
        else:
            year = '20' + match.group(3)
        candidate = '-'.join([year, month, day])
        replacement[candidate] = candidates[item]
    candidates = Counter(replacement)
    catch = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})')
    yearpat = re.compile(r'^([0-9]{4})')
    bestmatch = select_candidate(candidates, catch, yearpat)
    result = filter_ymd_candidate(bestmatch, pattern, copyear, outputformat)
    if result is not None:
        return result

    ## 2 components
    logger.debug('switching to two components')
    #
    pattern = re.compile(r'\D([0-9]{4}[/.-][0-9]{2})\D')
    yearpat = re.compile(r'^\D?([12][0-9]{3})')
    catch = re.compile(r'([0-9]{4})[/.-]([0-9]{2})')
    candidates = plausible_year_filter(htmlstring, pattern, yearpat)
    bestmatch = select_candidate(candidates, catch, yearpat)
    # bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), '01'])
        if date_validator(pagedate, '%Y-%m-%d') is True:
            if copyear == 0 or int(bestmatch.group(1)) >= copyear:
                logger.debug('date found for pattern "%s": %s', pattern, pagedate)
                return convert_date(pagedate, '%Y-%m-%d', outputformat)
    #
    pattern = re.compile(r'\D([0-3]?[0-9][/.-][0-9]{4})\D')
    yearpat = re.compile(r'([12][0-9]{3})\D?$')
    candidates = plausible_year_filter(htmlstring, pattern, yearpat)
    # revert DD-MM-YYYY patterns before sorting
    replacement = dict()
    for item in candidates:
        match = re.match(r'([0-3]?[0-9])[/.-]([0-9]{4})', item)
        if len(match.group(1)) == 1:
            month = '0' + match.group(1)
        else:
            month = match.group(1)
        candidate = '-'.join([match.group(2), month, '01'])
        replacement[candidate] = candidates[item]
    candidates = Counter(replacement)
    catch = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})')
    yearpat = re.compile(r'^([0-9]{4})')
    # select
    bestmatch = select_candidate(candidates, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), bestmatch.group(3)])
        if date_validator(pagedate, '%Y-%m-%d') is True:
            if copyear == 0 or int(bestmatch.group(1)) >= copyear:
                logger.debug('date found for pattern "%s": %s', pattern, pagedate)
                return convert_date(pagedate, '%Y-%m-%d', outputformat)

    ## 1 component
    logger.debug('switching to one component')
    # last try
    # pattern = '(\D19[0-9]{2}\D|\D20[0-9]{2}\D)'
    pattern = re.compile(r'\D([12][0-9]{3})\D')
    yearpat = re.compile(r'^\D?([12][0-9]{3})')
    catch = re.compile(r'^\D?([12][0-9]{3})')
    candidates = plausible_year_filter(htmlstring, pattern, yearpat)
    bestmatch = select_candidate(candidates, catch, yearpat)
    # bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(0), '01', '01'])
        if date_validator(pagedate, '%Y-%m-%d') is True:
            if copyear == 0 or int(bestmatch.group(0)) >= copyear:
                logger.debug('date found for pattern "%s": %s', pattern, pagedate)
                return convert_date(pagedate, '%Y-%m-%d', outputformat)

    # catchall
    if copyear != 0:
        pagedate = '-'.join([str(copyear), '01', '01'])
        return convert_date(pagedate, '%Y-%m-%d', outputformat)
    return None


#@profile
def load_html(htmlobject):
    """Load object given as input and validate its type (accepted: LXML tree and string)"""
    if isinstance(htmlobject, (etree._ElementTree, html.HtmlElement)):
        # copy tree
        tree = htmlobject
        # derive string
        htmlstring = html.tostring(htmlobject, encoding='unicode')
    elif isinstance(htmlobject, str):
        # the string is a URL, download it
        if re.match(r'https?://', htmlobject):
            logger.info('URL detected, downloading: %s', htmlobject)
            htmltext = fetch_url(htmlobject)
            if htmltext is not None:
                htmlstring = htmltext
        # copy string
        else:
            htmlstring = htmlobject
        ## robust parsing
        try:
            # parse
            tree = html.parse(StringIO(htmlstring), parser=HTML_PARSER)
            # tree = html.fromstring(html.encode('utf8'), parser=parser)
        except UnicodeDecodeError as err:
            logger.error('unicode %s', err)
            tree = None
        except UnboundLocalError as err:
            logger.error('parsed string %s', err)
            tree = None
        except (etree.XMLSyntaxError, ValueError, AttributeError) as err:
            logger.error('parser %s', err)
            tree = None
    else:
        logger.error('this type cannot be processed: %s', type(htmlobject))
        tree = None
        htmlstring = None
    return (tree, htmlstring)


#@profile
def find_date(htmlobject, extensive_search=True, outputformat='%Y-%m-%d', url=None):
    """Main function: apply a series of techniques to date the document, from safe to adventurous"""
    # init
    tree, htmlstring = load_html(htmlobject)
    find_date.extensive_search = extensive_search
    logger.debug('starting')

    # safety
    if tree is None:
        return None
    if outputformat != '%Y-%m-%d' and output_format_validator(outputformat) is False:
        return None

    # URL
    if url is None:
        # link canonical
        for elem in tree.xpath('//link[@rel="canonical"]'):
            if 'href' in elem.attrib:
                url = elem.get('href')
    if url is not None:
        dateresult = extract_url_date(url, outputformat)
        if dateresult is not None:
            return dateresult

    # first, try header
    pagedate = examine_header(tree, outputformat)
    if pagedate is not None and date_validator(pagedate, outputformat) is True:
        return pagedate

    # <abbr>
    elements = tree.xpath('//abbr')
    if elements is not None: # and len(elements) > 0:
        reference = 0
        for elem in elements:
            # data-utime (mostly Facebook)
            if 'data-utime' in elem.attrib:
                try:
                    candidate = int(elem.get('data-utime'))
                except ValueError:
                    continue
                logger.debug('data-utime found: %s', candidate)
                # look for newest (i.e. largest time delta)
                if candidate > reference:
                    reference = candidate
            # class
            if 'class' in elem.attrib:
                if elem.get('class') == 'published' or elem.get('class') == 'date-published':
                    # other attributes
                    if 'title' in elem.attrib:
                        trytext = elem.get('title')
                        logger.debug('abbr published-title found: %s', trytext)
                        reference = compare_reference(reference, trytext, outputformat)
                    # dates, not times of the day
                    if elem.text and len(elem.text) > 10:
                        trytext = re.sub(r'^am ', '', elem.text)
                        logger.debug('abbr published found: %s', trytext)
                        reference = compare_reference(reference, trytext, outputformat)
        # convert and return
        if reference > 0:
            dateobject = datetime.datetime.fromtimestamp(reference)
            converted = dateobject.strftime(outputformat)
            # quality control
            if date_validator(converted, outputformat) is True:
                return converted
        # try rescue in abbr content
        else:
            dateresult = examine_date_elements(tree, '//abbr', outputformat)
            if dateresult is not None and date_validator(dateresult, outputformat) is True:
                return dateresult # break

    # expressions + text_content
    for expr in DATE_EXPRESSIONS:
        dateresult = examine_date_elements(tree, expr, outputformat)
        if dateresult is not None and date_validator(dateresult, outputformat) is True:
            return dateresult # break

    # <time>
    elements = tree.xpath('//time')
    if elements is not None: # and len(elements) > 0:
        # scan all the tags and look for the newest one
        reference = 0
        for elem in elements:
            # go for datetime
            if 'datetime' in elem.attrib and len(elem.get('datetime')) > 6:
                # first choice: entry-date + datetime attribute
                if 'class' in elem.attrib:
                    if elem.get('class').startswith('entry-date') or elem.get('class').startswith('entry-time') or elem.get('class') == 'updated':
                        logger.debug('time/datetime found: %s', elem.get('datetime'))
                        reference = compare_reference(reference, elem.get('datetime'), outputformat)
                        if reference > 0:
                            break
                # datetime attribute
                else:
                    logger.debug('time/datetime found: %s', elem.get('datetime'))
                    reference = compare_reference(reference, elem.get('datetime'), outputformat)
            # bare text in element
            elif elem.text is not None and len(elem.text) > 6:
                logger.debug('time/datetime found: %s', elem.text)
                reference = compare_reference(reference, elem.text, outputformat)
            # else...
        # return
        if reference > 0:
            # convert and return
            dateobject = datetime.datetime.fromtimestamp(reference)
            converted = dateobject.strftime(outputformat)
            # quality control
            if date_validator(converted, outputformat) is True:
                return converted

    # URL 2
    if url is not None:
        dateresult = extract_partial_url_date(url, outputformat)
        if dateresult is not None:
            return dateresult

    # clean before string search
    cleaned_html = cleaner.clean_html(tree)
    htmlstring = html.tostring(cleaned_html, encoding='unicode')
    # remove comments by hand as faulty in lxml
    # htmlstring = re.sub(r'<!--.+?-->', '', htmlstring, flags=re.DOTALL)
    logger.debug('html cleaned')

    # date regex timestamp rescue
    json_match = json_pattern.search(htmlstring)
    if json_match and date_validator(json_match.group(1), '%Y-%m-%d') is True:
        logger.debug('JSON time found: %s', json_match.group(0))
        return convert_date(json_match.group(1), '%Y-%m-%d', outputformat)
    timestamp_match = timestamp_pattern.search(htmlstring)
    if timestamp_match and date_validator(timestamp_match.group(1), '%Y-%m-%d') is True:
        logger.debug('time regex found: %s', timestamp_match.group(0))
        return convert_date(timestamp_match.group(1), '%Y-%m-%d', outputformat)

    # precise German patterns
    de_match = german_pattern.search(htmlstring)
    if de_match and len(de_match.group(3)) in (2, 4):
        try:
            if len(de_match.group(3)) == 2:
                candidate = datetime.date(int('20' + de_match.group(3)), int(de_match.group(2)), int(de_match.group(1)))
            else:
                candidate = datetime.date(int(de_match.group(3)), int(de_match.group(2)), int(de_match.group(1)))
        except ValueError:
            logger.debug('value error: %s', de_match.group(0))
        else:
            if date_validator(candidate, '%Y-%m-%d') is True:
                logger.debug('precise pattern found: %s', de_match.group(0))
                return convert_date(candidate, '%Y-%m-%d', outputformat)

    # last resort
    if extensive_search is True:
        logger.debug('extensive search started')
        pagedate = search_page(htmlstring, outputformat)
        return pagedate

    return None

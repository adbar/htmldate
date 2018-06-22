# -*- coding: utf-8 -*-
"""
Module bundling all functions needed to determine the date of HTML strings or LXML trees.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license

# compatibility
from __future__ import absolute_import, division, print_function, unicode_literals

# from future import standard_library
# standard_library.install_aliases()

# standard
import datetime
import logging
import re
import sys
import time

# from codecs import open
from collections import Counter

try:
    from cStringIO import StringIO # Python 2
except ImportError:
    from io import StringIO # Python 3

# third-party
import dateparser
from lxml import etree, html
from lxml.html.clean import Cleaner

# own
from .download import fetch_url
# import settings

# compatibility by isinstance
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY3:
    STRING_TYPES = str
else:
    STRING_TYPES = basestring



## TODO:
# simplify! (date search in text; )
# speed benchmark
# from og:image or <img>?
# MODIFIED vs CREATION date switch?
# .lower() in tags and attributes?
# 



## INIT
logger = logging.getLogger(__name__)

DATE_EXPRESSIONS = ["//*[starts-with(@id, 'date')]", "//*[starts-with(@class, 'date')]", "//*[starts-with(@id, 'time')]", "//*[starts-with(@class, 'time')]", "//*[starts-with(@class, 'byline')]", "//*[starts-with(@class, 'entry-date')]", "//*[starts-with(@class, 'post-meta')]", "//*[starts-with(@class, 'postmetadata')]", "//*[starts-with(@itemprop, 'date')]", "//span[starts-with(@class, 'field-content')]", "//*[contains(@class, 'date')]", "//*[contains(@id, 'lastmod')]", "//*[starts-with(@class, 'entry-time')]"]

#
# time-ago datetime=
# relative-time datetime=
# timestamp
# data-utime
# ...


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


cleaner = Cleaner()
cleaner.comments = True
cleaner.embedded = True
cleaner.forms = False
cleaner.frames = True
cleaner.javascript = False
cleaner.links = False
cleaner.meta = False
cleaner.page_structure = True
cleaner.processing_instructions = True
cleaner.remove_unknown_tags = False
cleaner.safe_attrs_only = False
cleaner.scripts = False
cleaner.style = False
cleaner.kill_tags = ['audio', 'canvas', 'label', 'map', 'math', 'object', 'picture', 'table', 'svg', 'video']
# 'embed', 'figure', 'img',


def date_validator(datestring, outputformat):
    """Validate a string with respect to the chosen outputformat and basic heuristics"""
    # try if date can be parsed using chosen outputformat
    try:
        dateobject = datetime.datetime.strptime(datestring, outputformat)
    except ValueError:
        return False
    # basic year validation
    year = int(datetime.date.strftime(dateobject, '%Y'))
    if MIN_YEAR <= year <= MAX_YEAR:
        # not newer than today
        if dateobject.date() <= TODAY:
            return True
    logger.debug('date not valid: %s', datestring)
    return False


def output_format_validator(outputformat):
    """Validate the output format in the settings"""
    # test in abstracto
    if not isinstance(outputformat, STRING_TYPES) or not '%' in outputformat:
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


def convert_date(datestring, inputformat, outputformat):
    """Parse date and return string in desired format"""
    dateobject = datetime.datetime.strptime(datestring, inputformat)
    converted = dateobject.strftime(outputformat)
    return converted


def try_ymd_date(string, outputformat, parser):
    """Use dateparser to parse the assumed date expression"""
    if string is None or len(string) < 4:
        return None

    # faster than fire dateparser at once
    if re.match(r'[0-9]{4}', string):
        # simple case
        result = re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}(?=(\D|$))', string)
        if result is not None and date_validator(result.group(0), '%Y-%m-%d') is True:
            logger.debug('result: %s', result.group(0))
            converted = convert_date(result.group(0), '%Y-%m-%d', outputformat)
            if date_validator(converted, outputformat) is True:
                return converted
        # '201709011234' not covered by dateparser
        result = re.match(r'[0-9]{8}', string)
        if result is not None:
            temp = result.group(0)
            candidate = '-'.join((temp[0:4], temp[4:6], temp[6:8]))
            if date_validator(candidate, '%Y-%m-%d') is True:
                logger.debug('result: %s', candidate)
                converted = convert_date(candidate, '%Y-%m-%d', outputformat)
                if date_validator(converted, outputformat) is True:
                    return converted

    # send to dateparser
    # target = dateparser.parse(string, settings={'PREFER_DAY_OF_MONTH': 'first', 'PREFER_DATES_FROM': 'past', 'DATE_ORDER': 'DMY'})
    # but in dateparser: 00:00:00
    if string != '00:00:00':
        target = parser.get_date_data(string)['date_obj']
        if target is not None:
            logger.debug('result: %s', target)
            datestring = datetime.date.strftime(target, outputformat)
            if date_validator(datestring, outputformat) is True:
                return datestring
    # catchall
    return None


def extract_url_date(testurl, outputformat):
    """Extract the date out of an URL string"""
    # easy extract in Y-M-D format
    if re.search(r'[0-9]{4}/[0-9]{2}/[0-9]{2}', testurl):
        dateresult = re.search(r'[0-9]{4}/[0-9]{2}/[0-9]{2}', testurl).group(0)
        logger.debug('found date in URL: %s', dateresult)
        try:
            converted = convert_date(dateresult, '%Y/%m/%d', outputformat)
            if date_validator(converted, outputformat) is True:
                return converted
        except ValueError as err:
            logger.debug('value error during conversion: %s %s', dateresult, err)
    # catchall
    return None


def examine_date_elements(tree, expression, outputformat, parser):
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
            # simple length heuristics
            textcontent = elem.text_content().strip()
            if not textcontent or len(textcontent) < 3:
                continue
            elif not re.search(r'\d', textcontent):
                continue
            else:
                # try a first part
                toexamine = textcontent[:30]
                logger.debug('analyzing: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                attempt = try_ymd_date(toexamine, outputformat, parser)
                if attempt is not None:
                    return attempt
                # try a shorter first segment
                else:
                    toexamine = re.sub(r'[^0-9\.-]+', '', toexamine)
                    if len(toexamine) < 6:
                        continue
                    logger.debug('re-analyzing: %s', toexamine)
                    attempt = try_ymd_date(toexamine, outputformat, parser)
                    if attempt is not None:
                        return attempt
    # catchall
    return None


def examine_header(tree, outputformat, parser):
    """Parse header elements to find date cues"""
    headerdate = None
    reserve = None
    try:
        # link canonical
        for elem in tree.xpath('//link[@rel="canonical"]'):
            if 'href' in elem.attrib:
                dateresult = extract_url_date(elem.get('href'), outputformat)
                if dateresult is not None:
                    return dateresult
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
                    headerdate = try_ymd_date(elem.get('content'), outputformat, parser)
                # modified: override published_time
                elif elem.get('property').lower() in ('article:modified_time', 'og:article:modified_time', 'og:updated_time'):
                    logger.debug('examining meta property: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    attempt = try_ymd_date(elem.get('content'), outputformat, parser)
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
                elif elem.get('name').lower() in ('article.created', 'article_date_original', 'article.published', 'created', 'cxenseparse:recs:publishtime', 'date', 'date_published', 'dc.date', 'dc.date.created', 'dc.date.issued', 'dcterms.date', 'gentime', 'lastmodified', 'og:published_time', 'originalpublicationdate', 'pubdate', 'publishdate', 'published-date', 'publication_date', 'sailthru.date', 'timestamp'):
                    logger.debug('examining meta name: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    headerdate = try_ymd_date(elem.get('content'), outputformat, parser)
            elif headerdate is None and 'pubdate' in elem.attrib:
                if elem.get('pubdate').lower() == 'pubdate':
                    logger.debug('examining meta pubdate: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    headerdate = try_ymd_date(elem.get('content'), outputformat, parser)
            # other types # itemscope?
            elif headerdate is None and 'itemprop' in elem.attrib:
                if elem.get('itemprop').lower() in ('datecreated', 'datepublished', 'pubyear') and headerdate is None:
                    logger.debug('examining meta itemprop: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    if 'datetime' in elem.attrib:
                        headerdate = try_ymd_date(elem.get('datetime'), outputformat, parser)
                    elif 'content' in elem.attrib:
                        headerdate = try_ymd_date(elem.get('content'), outputformat, parser)
                # override
                elif elem.get('itemprop').lower() == 'datemodified':
                    logger.debug('examining meta itemprop: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    if 'datetime' in elem.attrib:
                        attempt = try_ymd_date(elem.get('datetime'), outputformat, parser)
                    elif 'content' in elem.attrib:
                        attempt = try_ymd_date(elem.get('content'), outputformat, parser)
                    if attempt is not None:
                        headerdate = attempt
                # reserve with copyrightyear
                elif headerdate is None and elem.get('itemprop').lower() == 'copyrightyear':
                    logger.debug('examining meta itemprop: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    if 'content' in elem.attrib:
                        attempt = '-'.join([elem.get('content'), '07', '01'])
                        if date_validator(attempt, '%Y-%m-%d') is True:
                            reserve = attempt
            # http-equiv, rare http://www.standardista.com/html5/http-equiv-the-meta-attribute-explained/
            elif headerdate is None and 'http-equiv' in elem.attrib:
                if elem.get('http-equiv').lower() in ('date', 'last-modified') and headerdate is None:
                    logger.debug('examining meta http-equiv: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    headerdate = try_ymd_date(elem.get('content'), outputformat, parser)
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


def plausible_year_filter(htmlstring, pattern, yearpat, tocomplete=False):
    """Filter the date patterns to find plausible years only"""
    occurrences = Counter(re.findall(r'%s' % pattern, htmlstring))
    toremove = set()
    # logger.debug('occurrences: %s', occurrences)
    for item in occurrences.keys():
        # scrap implausible dates
        try:
            if tocomplete is False:
                potential_year = int(re.search(r'%s' % yearpat, item).group(1))
            else:
                lastdigits = re.search(r'%s' % yearpat, item).group(1)
                if re.match(r'9', lastdigits):
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


def select_candidate(occurrences, catch, yearpat):
    """Select a candidate among the most frequent matches"""
    # logger.debug('occurrences: %s', occurrences)
    if len(occurrences) == 0:
        return
    elif len(occurrences) == 1:
        match = re.search(r'%s' % catch, list(occurrences.keys())[0])
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
        match = re.search(r'%s' % catch, first_pattern)
    else:
        year1 = int(re.search(r'%s' % yearpat, first_pattern).group(1))
        year2 = int(re.search(r'%s' % yearpat, second_pattern).group(1))
        # safety net: plausibility
        if date_validator(str(year1), '%Y') is False:
            if date_validator(str(year2), '%Y') is True:
                # logger.debug('first candidate not suitable: %s', year1)
                match = re.match(r'%s' % catch, second_pattern)
            else:
                logger.debug('no suitable candidate: %s %s', year1, year2)
                return None
        # safety net: newer date but up to 50% less frequent
        if year2 > year1 and second_count/first_count > 0.5:
            match = re.match(r'%s' % catch, second_pattern)
        # not newer or hopefully not significant
        else:
            match = re.match(r'%s' % catch, first_pattern)
    if match:
        return match
    return None


def filter_ymd_candidate(bestmatch, pattern, copyear, outputformat):
    """Filter free text candidates in the YMD format"""
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), bestmatch.group(3)])
        if date_validator(pagedate, '%Y-%m-%d') is True:
            if copyear == 0 or int(bestmatch.group(1)) >= copyear:
                logger.debug('date found for pattern "%s": %s', pattern, pagedate)
                return convert_date(pagedate, '%Y-%m-%d', outputformat)


def search_pattern(htmlstring, pattern, catch, yearpat):
    """Chained candidate filtering and selection"""
    candidates = plausible_year_filter(htmlstring, pattern, yearpat)
    return select_candidate(candidates, catch, yearpat)


def search_page(htmlstring, outputformat):
    """Search the page for common patterns (can lead to flawed results!)"""
    # init
    # pagedate = None

    # date ultimate rescue for the rest: most frequent year/month comination in the HTML
    ## this is risky

    # copyright symbol
    logger.debug('looking for copyright/footer information')
    copyear = 0
    pattern = '(?:©|&copy;|\(c\))\D+([12][0-9]{3})\D'
    yearpat = '^\D?([12][0-9]{3})'
    candidates = plausible_year_filter(htmlstring, pattern, yearpat)
    catch = '^\D?([12][0-9]{3})'
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
    pattern = '/([0-9]{4}/[0-9]{2}/[0-9]{2})[01/]'
    yearpat = '^\D?([12][0-9]{3})'
    candidates = plausible_year_filter(htmlstring, pattern, yearpat)
    catch = '([0-9]{4})/([0-9]{2})/([0-9]{2})'
    bestmatch = select_candidate(candidates, catch, yearpat)
    # bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    result = filter_ymd_candidate(bestmatch, pattern, copyear, outputformat)
    if result is not None:
        return result

    # more loosely structured data
    pattern = '\D([0-9]{4}[/.-][0-9]{2}[/.-][0-9]{2})\D'
    yearpat = '^\D?([12][0-9]{3})'
    candidates = plausible_year_filter(htmlstring, pattern, yearpat)
    catch = '([0-9]{4})[/.-]([0-9]{2})[/.-]([0-9]{2})'
    bestmatch = select_candidate(candidates, catch, yearpat)
    # bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    result = filter_ymd_candidate(bestmatch, pattern, copyear, outputformat)
    if result is not None:
        return result

    #
    pattern = '\D([0-3]?[0-9][/.-][01]?[0-9][/.-][0-9]{4})\D'
    yearpat = '(19[0-9]{2}|20[0-9]{2})\D?$'
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
    catch = '([0-9]{4})-([0-9]{2})-([0-9]{2})'
    yearpat = '^([0-9]{4})'
    # select
    bestmatch = select_candidate(candidates, catch, yearpat)
    result = filter_ymd_candidate(bestmatch, pattern, copyear, outputformat)
    if result is not None:
        return result

    # valid dates strings
    pattern = '(\D19[0-9]{2}[01][0-9][0-3][0-9]\D|\D20[0-9]{2}[01][0-9][0-3][0-9]\D)'
    yearpat = '^\D?([12][0-9]{3})'
    candidates = plausible_year_filter(htmlstring, pattern, yearpat)
    catch = '([12][0-9]{3})([01][0-9])([0-3][0-9])'
    bestmatch = select_candidate(candidates, catch, yearpat)
    # bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    result = filter_ymd_candidate(bestmatch, pattern, copyear, outputformat)
    if result is not None:
        return result

    # DD?/MM?/YY
    pattern = '\D([0-3]?[0-9][/.][01]?[0-9][/.][019][0-9])\D'
    yearpat = '([0-9]{2})$'
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
        if re.match(r'9', match.group(3)):
            year = '19' + match.group(3)
        else:
            year = '20' + match.group(3)
        candidate = '-'.join([year, month, day])
        replacement[candidate] = candidates[item]
    candidates = Counter(replacement)
    catch = '([0-9]{4})-([0-9]{2})-([0-9]{2})'
    yearpat = '^([0-9]{4})'
    bestmatch = select_candidate(candidates, catch, yearpat)
    result = filter_ymd_candidate(bestmatch, pattern, copyear, outputformat)
    if result is not None:
        return result

    ## 2 components
    logger.debug('switching to two components')
    #
    pattern = '\D([0-9]{4}[/.-][0-9]{2})\D'
    yearpat = '^\D?([12][0-9]{3})'
    candidates = plausible_year_filter(htmlstring, pattern, yearpat)
    catch = '([0-9]{4})[/.-]([0-9]{2})'
    bestmatch = select_candidate(candidates, catch, yearpat)
    # bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), '01'])
        if date_validator(pagedate, '%Y-%m-%d') is True:
            if copyear == 0 or int(bestmatch.group(1)) >= copyear:
                logger.debug('date found for pattern "%s": %s', pattern, pagedate)
                return convert_date(pagedate, '%Y-%m-%d', outputformat)
    #
    pattern = '\D([0-3]?[0-9][/.-][0-9]{4})\D'
    yearpat = '([12][0-9]{3})\D?$'
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
    catch = '([0-9]{4})-([0-9]{2})-([0-9]{2})'
    yearpat = '^([0-9]{4})'
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
    pattern = '\D([12][0-9]{3})\D'
    yearpat = '^\D?([12][0-9]{3})'
    candidates = plausible_year_filter(htmlstring, pattern, yearpat)
    catch = '^\D?([12][0-9]{3})'
    bestmatch = select_candidate(candidates, catch, yearpat)
    # bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(0), '07', '01'])
        if date_validator(pagedate, '%Y-%m-%d') is True:
            if copyear == 0 or int(bestmatch.group(0)) >= copyear:
                logger.debug('date found for pattern "%s": %s', pattern, pagedate)
                return convert_date(pagedate, '%Y-%m-%d', outputformat)

    # catchall
    if copyear != 0:
        pagedate = '-'.join([str(copyear), '07', '01'])
        return convert_date(pagedate, '%Y-%m-%d', outputformat)
    return None


def load_html(htmlobject):
    """Load object given as input and validate its type (accepted: LXML tree and string)"""
    if isinstance(htmlobject, (etree._ElementTree, html.HtmlElement)):
        # copy tree
        tree = htmlobject
        # derive string
        htmlstring = html.tostring(htmlobject, encoding='unicode')
    elif isinstance(htmlobject, STRING_TYPES):
        # the string is a URL, download it
        if re.match(r'https?://', htmlobject):
            logger.info('URL detected, downloading: %s', htmlobject)
            rget = fetch_url(htmlobject)
            if rget is not None:
                htmlstring = rget.text
        # copy string
        else:
            htmlstring = htmlobject
        ## robust parsing
        try:
            # parse
            parser = html.HTMLParser() # encoding='utf8'
            tree = html.parse(StringIO(htmlstring), parser=parser)
            ## TODO: clean page?
            # tree = html.fromstring(html.encode('utf8'), parser=parser)
            # <svg>
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


def find_date(htmlobject, extensive_search=True, outputformat='%Y-%m-%d', dparser=dateparser.DateDataParser(settings=PARSERCONFIG), url=None):
    """Main function: apply a series of techniques to date the document, from safe to adventurous"""
    # init
    tree, htmlstring = load_html(htmlobject)
    # safety
    if tree is None:
        return
    if output_format_validator(outputformat) is False:
        return

    # URL
    if url is not None:
        dateresult = extract_url_date(url, outputformat)
        if dateresult is not None:
            return dateresult

    # first, try header
    pagedate = examine_header(tree, outputformat, dparser)
    if pagedate is not None and date_validator(pagedate, outputformat) is True:
        return pagedate

    # <time>
    elements = tree.xpath('//time')
    if elements is not None and len(elements) > 0:
        # scan all the tags and look for the newest one
        reference = 0
        for elem in elements:
            # go for datetime
            if 'datetime' in elem.attrib and len(elem.get('datetime')) > 6:
                # first choice: entry-date + datetime attribute
                if 'class' in elem.attrib:
                    if elem.get('class').startswith('entry-date'):
                        attempt = try_ymd_date(elem.get('datetime'), outputformat, dparser)
                        if attempt is not None:
                            reference = time.mktime(datetime.datetime.strptime(attempt, outputformat).timetuple())
                            logger.debug('time/datetime found: %s %s', elem.get('datetime'), reference)
                            break
                # datetime attribute
                else:
                    attempt = try_ymd_date(elem.get('datetime'), outputformat, dparser)
                    if attempt is not None: # and date_validator(attempt, outputformat) is True:
                        timestamp = time.mktime(datetime.datetime.strptime(attempt, outputformat).timetuple())
                        if timestamp > reference:
                            logger.debug('time/datetime found: %s %s', elem.get('datetime'), timestamp)
                            reference = timestamp
            # bare text in element
            elif elem.text is not None and len(elem.text) > 6:
                attempt = try_ymd_date(elem.text, outputformat, dparser)
                if attempt is not None: # and date_validator(attempt, outputformat) is True:
                    timestamp = time.mktime(datetime.datetime.strptime(attempt, outputformat).timetuple())
                    if timestamp > reference:
                        logger.debug('time/datetime found: %s %s', elem.text, timestamp)
                        reference = timestamp
           # else...
           # ...
        # return
        if reference > 0:
            # convert and return
            dateobject = datetime.datetime.fromtimestamp(reference)
            converted = dateobject.strftime(outputformat)
            # quality control
            if date_validator(converted, outputformat) is True:
                return converted

    # <abbr>
    elements = tree.xpath('//abbr')
    if elements is not None and len(elements) > 0:
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
                    # dates, not times of the day
                    if elem.text and len(elem.text) > 10:
                        trytext = re.sub(r'^am ', '', elem.text)
                        logger.debug('abbr published found: %s', trytext)
                        attempt = try_ymd_date(elem.text, outputformat, dparser)
                        if attempt is not None: # and date_validator(attempt, outputformat) is True:
                            reference = time.mktime(datetime.datetime.strptime(attempt, outputformat).timetuple())
        # convert and return
        if reference > 0:
            dateobject = datetime.datetime.fromtimestamp(reference)
            converted = dateobject.strftime(outputformat)
            # quality control
            if date_validator(converted, outputformat) is True:
                return converted

    # expressions + text_content
    for expr in DATE_EXPRESSIONS:
        dateresult = examine_date_elements(tree, expr, outputformat, dparser)
        if dateresult is not None and date_validator(dateresult, outputformat) is True:
            return dateresult # break

    # clean before string search
    cleaned_html = cleaner.clean_html(tree)
    htmlstring = html.tostring(cleaned_html, encoding='unicode')
    # remove comments by hand as faulty in lxml
    htmlstring = re.sub(r'<!--.+?-->', '', htmlstring, flags=re.DOTALL)
    logger.debug('html cleaned')

    # date regex timestamp rescue
    match = re.search(r'([0-9]{4}-[0-9]{2}-[0-9]{2}).[0-9]{2}:[0-9]{2}:[0-9]{2}', htmlstring)
    if match and date_validator(match.group(1), '%Y-%m-%d') is True:
        logger.debug('time regex found: %s', match.group(0))
        return convert_date(match.group(1), '%Y-%m-%d', outputformat)

    # last resort
    if extensive_search is True:
        logger.debug('extensive search started')
        pagedate = search_page(htmlstring, outputformat)
        return pagedate

    # return pagedate

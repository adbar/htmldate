# -*- coding: utf-8 -*-
"""
Module bundling all needed functions.
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

# from codecs import open
from collections import Counter

try:
    from cStringIO import StringIO # Python 2
except ImportError:
    from io import StringIO # Python 3

# from six import text_type

# third-party
import dateparser
from lxml import etree, html

# own
# import settings


## INIT
logger = logging.getLogger(__name__)

DATE_EXPRESSIONS = ["//*[starts-with(@id, 'date')]", "//*[starts-with(@class, 'date')]", "//*[starts-with(@id, 'time')]", "//*[starts-with(@class, 'time')]", "//*[starts-with(@class, 'byline')]", "//*[starts-with(@class, 'entry-date')]", "//*[starts-with(@class, 'post-meta')]", "//*[starts-with(@class, 'postmetadata')]", "//*[starts-with(@itemprop, 'date')]", "//*[contains(@class, 'date')]", "//span[starts-with(@class, 'field-content')]"]

## TODO:
# speed benchmark
# from og:image or <img>?

# time-ago datetime=
# relative-time datetime=
# timestamp
# data-utime
# <div class="entry-date">
# ...


OUTPUTFORMAT = '%Y-%m-%d'

MIN_YEAR = 1995 # inclusive
TODAY = datetime.date.today()
MAX_YEAR = 2020 # inclusive

# MODIFIED vs CREATION date switch?



def date_validator(datestring):
    """Validate a string with respect to the chosen outputformat and basic heuristics"""
    # try if date can be parsed using chosen outputformat
    try:
        dateobject = datetime.datetime.strptime(datestring, OUTPUTFORMAT)
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


def output_format_validator():
    """Validate the output format in the settings"""
    dateobject = datetime.datetime(2017, 9, 1, 0, 0)
    try:
        datetime.datetime.strftime(dateobject, OUTPUTFORMAT)
    except (NameError, ValueError) as err:
        logging.error('wrong output format: %s %s', OUTPUTFORMAT, err)
        return False
    return True


def try_date(string):
    """Use dateparser to parse the assumed date expression"""
    if string is None or len(string) < 4:
        return None

    # faster than fire dateparser at once
    if OUTPUTFORMAT == '%Y-%m-%d' and re.match(r'[0-9]{4}', string):
        # simple case
        result = re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}(?=(\D|$))', string)
        if result is not None and date_validator(result.group(0)) is True:
            return result.group(0)
        # '201709011234' not covered by dateparser
        result = re.match(r'[0-9]{8}', string)
        if result is not None:
            temp = result.group(0)
            candidate = '-'.join((temp[0:4], temp[4:6], temp[6:8]))
            if date_validator(candidate) is True:
                return candidate

    # send to dateparser
    target = dateparser.parse(string, settings={'PREFER_DAY_OF_MONTH': 'first', 'PREFER_DATES_FROM': 'past', 'DATE_ORDER': 'DMY'})
    if target is not None:
        datestring = datetime.date.strftime(target, OUTPUTFORMAT)
        if date_validator(datestring) is True:
            return datestring
    return None


def examine_date_elements(tree, expression):
    """Check HTML elements one by one for date expressions"""
    try:
        elements = tree.xpath(expression)
    except etree.XPathEvalError as err:
        logger.error('lxml expression %s throws an error: %s', expression, err)
    else:
        if elements is not None:
            for elem in elements:
                # simple length heuristics
                textcontent = elem.text_content().strip()
                if 3 < len(textcontent) < 30 and re.search(r'\d', textcontent):
                    logger.debug('analyzing: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    attempt = try_date(elem.text_content().strip())
                    if attempt is not None:
                        logger.debug('result: %s', attempt)
                        if date_validator(attempt) is True:
                            return attempt
    # catchall
    return None


def examine_header(tree):
    """Parse header elements to find date cues"""
    headerdate = None
    # meta elements in header
    try:
        for elem in tree.xpath('//meta'): # was //head/meta
            # safeguard
            if len(elem.attrib) < 1:
                continue
            ## property attribute
            if 'property' in elem.attrib: # elem.get('property') is not None:
                # safeguard
                if elem.get('content') is None or len(elem.get('content')) < 1:
                    continue
                # "og:" for OpenGraph http://ogp.me/
                if elem.get('property').lower() in ('article:published_time', 'bt:pubdate', 'dc:created', 'dc:date', 'og:article:published_time', 'og:published_time', 'rnews:datepublished') and headerdate is None:
                    logger.debug('examining meta property: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    headerdate = try_date(elem.get('content'))
                # modified: override published_time
                elif elem.get('property').lower() in ('article:modified_time', 'og:article:modified_time', 'og:updated_time'):
                    logger.debug('examining meta property: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    attempt = try_date(elem.get('content'))
                    if attempt is not None:
                        headerdate = attempt
            # name attribute
            elif 'name' in elem.attrib and headerdate is None: # elem.get('name') is not None:
                # safeguard
                if elem.get('content') is None or len(elem.get('content')) < 1:
                    continue
                # date
                if elem.get('name').lower() in ('article.created', 'article_date_original', 'article.published', 'created', 'cxenseparse:recs:publishtime', 'date', 'date_published', 'dc.date', 'dc.date.created', 'dc.date.issued', 'dcterms.date', 'gentime', 'lastmodified', 'og:published_time', 'originalpublicationdate', 'pubdate', 'publishdate', 'published-date', 'publication_date', 'sailthru.date', 'timestamp'):
                    logger.debug('examining meta name: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    headerdate = try_date(elem.get('content'))
            # other types # itemscope?
            elif 'itemprop' in elem.attrib:
                if elem.get('itemprop').lower() in ('datecreated', 'datepublished', 'pubyear') and headerdate is None:
                    logger.debug('examining meta itemprop: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    if 'datetime' in elem.attrib:
                        headerdate = try_date(elem.get('datetime'))
                    elif 'content' in elem.attrib:
                        headerdate = try_date(elem.get('content'))
                # override
                elif elem.get('itemprop').lower() == 'datemodified':
                    logger.debug('examining meta itemprop: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    if 'datetime' in elem.attrib:
                        attempt = try_date(elem.get('datetime'))
                    elif 'content' in elem.attrib:
                        attempt = try_date(elem.get('content'))
                    if attempt is not None:
                        headerdate = attempt
            elif 'pubdate' in elem.attrib and headerdate is None:
                if elem.get('pubdate').lower() == 'pubdate':
                    logger.debug('examining meta pubdate: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    headerdate = try_date(elem.get('content'))
            # http-equiv, rare http://www.standardista.com/html5/http-equiv-the-meta-attribute-explained/
            elif 'http-equiv' in elem.attrib:
                if elem.get('http-equiv').lower() in ('date', 'last-modified') and headerdate is None:
                    logger.debug('examining meta http-equiv: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    headerdate = try_date(elem.get('content'))
            #else:
            #    logger.debug('not found: %s %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip(), elem.attrib)

    except etree.XPathEvalError as err:
        logger.error('XPath %s', err)
        return None

    if headerdate is not None and date_validator(headerdate) is True:
        return headerdate
    return None



def search_pattern(htmlstring, pattern, catch, yearpat):
    """Search the given regex pattern throughout the document and return the most frequent match"""
    ## TODO: refine and clean up
    occurrences = Counter(re.findall(r'%s' % pattern, htmlstring))
    toremove = set()
    # logger.debug('occurrences: %s', occurrences)
    for item in occurrences:
        # scrap implausible dates
        try:
            potential_year = int(re.search(r'%s' % yearpat, item).group(1))
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

    # select
    # logger.debug('occurrences: %s', occurrences)
    if len(occurrences) == 0:
        return
    elif len(occurrences) == 1:
        match = re.search(r'%s' % catch, list(occurrences.keys())[0])
        if match:
            return match
    # all values are 1 (rare)?
    else:
        # select among most frequent
        firstselect = occurrences.most_common(5)
        logger.debug('firstselect: %s', firstselect)
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
            # safety net: newer date but up to 50% less frequent
            if year2 > year1 and second_count/first_count > 0.5:
                match = re.match(r'%s' % catch, second_pattern)
            # not newer or hopefully not significant
            else:
                match = re.match(r'%s' % catch, first_pattern)
        if match:
            return match
    return None


def search_page(htmlstring):
    """Search the page for common patterns (can lead to flawed results!)"""
    # init
    pagedate = None

    # date ultimate rescue for the rest: most frequent year/month comination in the HTML
    ## this is risky

    ## 3 components
    # logger.debug('3 components')
    # target URL characteristics
    pattern = '/([0-9]{4}/[0-9]{2}/[0-9]{2})/'
    catch = '([0-9]{4})/([0-9]{2})/([0-9]{2})'
    yearpat = '^\D?([12][0-9]{3})'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), bestmatch.group(3)])
        if date_validator(pagedate) is True:
            logger.debug('date found for pattern "%s": %s', pattern, pagedate)
            return pagedate

    # more loosely structured data
    pattern = '\D([0-9]{4}[/.-][0-9]{2}[/.-][0-9]{2})\D'
    catch = '([0-9]{4})[/.-]([0-9]{2})[/.-]([0-9]{2})'
    yearpat = '^\D?([12][0-9]{3})'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), bestmatch.group(3)])
        if date_validator(pagedate) is True:
            logger.debug('date found for pattern "%s": %s', pattern, pagedate)
            return pagedate
    #
    pattern = '\D([0-9]{2}[/.-][0-9]{2}[/.-][0-9]{4})\D'
    catch = '([0-9]{2})[/.-]([0-9]{2})[/.-]([0-9]{4})'
    yearpat = '(19[0-9]{2}|20[0-9]{2})\D?$'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(3), bestmatch.group(2), bestmatch.group(1)])
        if date_validator(pagedate) is True:
            logger.debug('date found for pattern "%s": %s', pattern, pagedate)
            return pagedate

    # valid dates strings
    pattern = '(\D19[0-9]{2}[01][0-9][0-3][0-9]\D|\D20[0-9]{2}[01][0-9][0-3][0-9]\D)'
    catch = '([12][0-9]{3})([01][0-9])([0-3][0-9])'
    yearpat = '^\D?([12][0-9]{3})'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), bestmatch.group(3)])
        if date_validator(pagedate) is True:
            logger.debug('date found for pattern "%s": %s', pattern, pagedate)
            return pagedate

    ## 2 components
    logger.debug('switching to two components')
    #
    pattern = '\D([0-9]{4}[/.-][0-9]{2})\D'
    catch = '([0-9]{4})[/.-]([0-9]{2})'
    yearpat = '^\D?([12][0-9]{3})'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), '01'])
        if date_validator(pagedate) is True:
            logger.debug('date found for pattern "%s": %s', pattern, pagedate)
            return pagedate
    #
    pattern = '\D([0-9]{2}[/.-][0-9]{4})\D'
    catch = '([0-9]{2})[/.-]([0-9]{4})'
    yearpat = '([12][0-9]{3})\D?$'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(2), bestmatch.group(1), '01'])
        if date_validator(pagedate) is True:
            logger.debug('date found for pattern "%s": %s', pattern, pagedate)
            return pagedate

    ## 1 component
    # last try
    logger.debug('switching to one component')
    # pattern = '(\D19[0-9]{2}\D|\D20[0-9]{2}\D)'
    pattern = '\D([12][0-9]{3})\D'
    catch = '^\D?([12][0-9]{3})'
    yearpat = '^\D?([12][0-9]{3})'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(0), '07', '01'])
        if date_validator(pagedate) is True:
            logger.debug('date found for pattern "%s": %s', pattern, pagedate)
            return pagedate

    # catchall
    return None



def find_date(htmlstring, extensive_search=True):
    """Main function: apply a series of techniques to date the document, from safe to adventurous"""
    # init
    pagedate = None
    if output_format_validator() is False:
        return

    # robust parsing
    try:
        tree = html.parse(StringIO(htmlstring), html.HTMLParser())
        ## TODO: clean page?
        # <svg>
    except UnicodeDecodeError as err:
        logger.error('unicode %s', err)
        return None
    except UnboundLocalError as err:
        logger.error('parsed string %s', err)
        return None
    except (etree.XMLSyntaxError, ValueError, AttributeError) as err:
        logger.error('parser %s', err)
        return None

    # first, try header
    pagedate = examine_header(tree)
    if pagedate is not None and date_validator(pagedate) is True:
        return pagedate

    # <time>
    elements = tree.xpath('//time')
    if elements is not None:
        for elem in elements:
            if 'datetime' in elem.attrib:
                logger.debug('time datetime found: %s', elem.get('datetime'))
                attempt = try_date(elem.get('datetime'))
                if attempt is not None and date_validator(attempt) is True:
                    return attempt # break

    # expressions + text_content
    for expr in DATE_EXPRESSIONS:
        dateresult = examine_date_elements(tree, expr)
        if dateresult is not None and date_validator(dateresult) is True:
            return dateresult # break

    # date regex timestamp rescue
    match = re.search(r'([0-9]{4}-[0-9]{2}-[0-9]{2}).[0-9]{2}:[0-9]{2}:[0-9]{2}', htmlstring)
    if match and date_validator(match.group(1)) is True:
        return match.group(1)

    # last resort
    if extensive_search is True:
        logger.debug('extensive search started')
        pagedate = search_page(htmlstring)

    return pagedate

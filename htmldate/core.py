# -*- coding: utf-8 -*-
"""
Module bundling all needed functions.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license

## TODO:
# speed benchmark
# from og:image or <img>?

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
logger = logging.getLogger()

DATE_EXPRESSIONS = ["//*[starts-with(@id, 'date')]", "//*[starts-with(@class, 'date')]", "//*[starts-with(@id, 'time')]", "//*[starts-with(@class, 'time')]", "//*[starts-with(@class, 'byline')]", "//*[starts-with(@class, 'entry-date')]", "//*[starts-with(@class, 'post-meta')]", "//*[starts-with(@class, 'postmetadata')]", "//*[starts-with(@itemprop, 'date')]", "//*[contains(@class, 'date')]"]
# time-ago datetime=
# timestamp
# ...

EXTENSIVE_SEARCH_BOOL = True # adventurous mode

OUTPUTFORMAT = '%Y-%m-%d'

MIN_YEAR = 1995 # inclusive
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
        return True
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
        result = re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}(?=\D)', string)
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
                if 3 < len(elem.text_content().strip()) < 30:
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
        for elem in tree.xpath('//head/meta'):
            # safeguard
            if len(elem.attrib) < 1:
                continue
            ## property attribute
            if elem.get('property') is not None:
                # safeguard
                if elem.get('content') is None or len(elem.get('content')) < 1:
                    continue
                # "og:" for OpenGraph http://ogp.me/
                if elem.get('property') in ('article:published_time', 'bt:pubdate', 'dc:created', 'dc:date', 'og:article:published_time', 'og:published_time', 'rnews:datePublished'):
                    if headerdate is None:
                        attempt = try_date(elem.get('content'))
                        if attempt is not None:
                            headerdate = attempt
                # modified: override published_time
                elif elem.get('property') in ('article:modified_time', 'og:updated_time'):
                    attempt = try_date(elem.get('content'))
                    if attempt is not None:
                        headerdate = attempt
            # name attribute
            elif 'name' in elem.attrib: # elem.get('name') is not None:
                # safeguard
                if elem.get('content') is None or len(elem.get('content')) < 1:
                    continue
                # date
                elif elem.get('name') in ('article.created', 'article_date_original', 'article.published', 'created', 'cXenseParse:recs:publishtime', 'date', 'date_published', 'dc.date', 'dc.date.created', 'dc.date.issued', 'dcterms.date', 'gentime', 'lastmodified', 'og:published_time', 'originalpublicationdate', 'pubdate', 'publishdate', 'published-date', 'publication_date', 'sailthru.date', 'timestamp'):
                    if headerdate is None:
                        attempt = try_date(elem.get('content'))
                        if attempt is not None:
                            headerdate = attempt
            # other types
            # itemscope?
            elif elem.get('itemprop') in ('datecreated', 'datepublished', 'pubyear') or elem.get('pubdate') == 'pubdate':
                if headerdate is None:
                    attempt = try_date(elem.get('datetime'))
                    if attempt is not None:
                        headerdate = attempt
            # http-equiv, rare http://www.standardista.com/html5/http-equiv-the-meta-attribute-explained/
            elif elem.get('http-equiv') in ('date', 'last-modified'):
                if headerdate is None:
                    attempt = try_date(elem.get('content'))
                    if attempt is not None:
                        headerdate = attempt

    except etree.XPathEvalError as err:
        logger.error('XPath %s', err)
        return None

    if headerdate is not None and date_validator(headerdate) is True:
        return headerdate
    return None



def search_pattern(htmlstring, pattern, catch, yearpat):
    """Search the given regex pattern throughout the document and return the most frequent match"""
    occurrences = re.findall(r'%s' % pattern, htmlstring)
    if occurrences:
        if len(occurrences) == 1:
            match = re.match(r'%s' % catch, occurrences[0])
            if match:
                return match
        # check most frequent results
        else:
            ## TODO: refine
            firstselect = Counter(occurrences).most_common(4)
            #print(firstselect)
            bestones = sorted(firstselect, reverse=True)[:2]
            first_pattern = bestones[0][0]
            first_count = bestones[0][1]
            second_pattern = bestones[1][0]
            second_count = bestones[1][1]
            #print(bestones)
            # same number of occurrences: always take most recent
            if first_count == second_count:
                match = re.match(r'%s' % catch, first_pattern)
            else:
                year1 = int(re.search(r'%s' % yearpat, first_pattern).group(0))
                year2 = int(re.search(r'%s' % yearpat, second_pattern).group(0))
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
    """Search the page for common patterns (can be dangerous!)"""
    # init
    pagedate = None

    # date ultimate rescue for the rest: most frequent year/month comination in the HTML
    ## this is risky

    ## TODO: clean page?

    ## 3 components
    # target URL characteristics
    pattern = '/([0-9]{4}/[0-9]{2}/[0-9]{2})/'
    catch = '([0-9]{4})/([0-9]{2})/([0-9]{2})'
    yearpat = '^([12][0-9]{3})'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), bestmatch.group(3)])
        if date_validator(pagedate) is True:
            return pagedate

    # more loosely structured data
    pattern = '\D([0-9]{4}[/.-][0-9]{2}[/.-][0-9]{2})\D'
    catch = '([0-9]{4})[/.-]([0-9]{2})[/.-]([0-9]{2})'
    yearpat = '^([12][0-9]{3})'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), bestmatch.group(3)])
        if date_validator(pagedate) is True:
            return pagedate
    # 
    pattern = '\D([0-9]{2}[/.-][0-9]{2}[/.-][0-9]{4})\D'
    catch = '([0-9]{2})[/.-]([0-9]{2})[/.-]([0-9]{4})'
    yearpat = '(19[0-9]{2}|20[0-9]{2})$'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(3), bestmatch.group(2), bestmatch.group(1)])
        if date_validator(pagedate) is True:
            return pagedate

    # valid dates strings
    pattern = '\D(19[0-9]{2}[01][0-9][0-3][0-9])\D|\D(20[0-9]{2}[01][0-9][0-3][0-9])\D'
    catch = '([12][0-9]{3})([01][0-9])([0-3][0-9])'
    yearpat = '^([12][0-9]{3})'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), bestmatch.group(3)])
        if date_validator(pagedate) is True:
            return pagedate

    ## 2 components
    #
    pattern = '\D([0-9]{4}[/.-][0-9]{2})\D'
    catch = '([0-9]{4})[/.-]([0-9]{2})'
    yearpat = '^([12][0-9]{3})'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), '01'])
        if date_validator(pagedate) is True:
            return pagedate
    #
    pattern = '\D([0-9]{2}[/.-][0-9]{4})\D'
    catch = '([0-9]{2})[/.-]([0-9]{4})'
    yearpat = '([12][0-9]{3})$'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(2), bestmatch.group(1), '01'])
        if date_validator(pagedate) is True:
            return pagedate

    ## 1 component
    # last try
    pattern = '\D(2[01][0-9]{2})\D'
    catch = '(2[01][0-9]{2})'
    yearpat = '^(2[01][0-9]{2})'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(0), '07', '01'])
        if date_validator(pagedate) is True:
            return pagedate

    # catchall
    return None



def find_date(htmlstring):
    """Main function: apply a series of techniques to date the document, from safe to adventurous"""
    # init
    pagedate = None
    if output_format_validator() is False:
        return

    # robust parsing
    try:
        tree = html.parse(StringIO(htmlstring), html.HTMLParser())
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
    if EXTENSIVE_SEARCH_BOOL is True:
        pagedate = search_page(htmlstring)

    return pagedate

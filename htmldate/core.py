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
from lxml.html.clean import Cleaner

# own
# import settings

## TODO:
# write helper around conversion
# take list of URLs as input
# more examples and tests
# speed benchmark
# from og:image or <img>?
# MODIFIED vs CREATION date switch?


## INIT
logger = logging.getLogger(__name__)

DATE_EXPRESSIONS = ["//*[starts-with(@id, 'date')]", "//*[starts-with(@class, 'date')]", "//*[starts-with(@id, 'time')]", "//*[starts-with(@class, 'time')]", "//*[starts-with(@class, 'byline')]", "//*[starts-with(@class, 'entry-date')]", "//*[starts-with(@class, 'post-meta')]", "//*[starts-with(@class, 'postmetadata')]", "//*[starts-with(@itemprop, 'date')]", "//span[starts-with(@class, 'field-content')]", "//*[contains(@class, 'date')]"]
# time-ago datetime=
# relative-time datetime=
# timestamp
# data-utime
# ...

MIN_YEAR = 1995 # inclusive
TODAY = datetime.date.today()
MAX_YEAR = datetime.date.today().year # inclusive # was 2020

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
    dateobject = datetime.datetime(2017, 9, 1, 0, 0)
    try:
        # datetime.datetime.strftime(dateobject, outputformat)
        dateobject.strftime(outputformat)
    except (NameError, ValueError) as err:
        logging.error('wrong output format: %s %s', outputformat, err)
        return False
    return True


def convert_date(datestring, inputformat, outputformat):
    """Parse date and return string in desired format"""
    dateobject = datetime.datetime.strptime(datestring, inputformat)
    converted = dateobject.strftime(outputformat)
    return converted


def try_ymd_date(string, outputformat):
    """Use dateparser to parse the assumed date expression"""
    if string is None or len(string) < 4:
        return None

    # faster than fire dateparser at once
    if re.match(r'[0-9]{4}', string):
        # simple case
        result = re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}(?=(\D|$))', string)
        if result is not None and date_validator(result.group(0), '%Y-%m-%d') is True:
            return convert_date(result.group(0), '%Y-%m-%d', outputformat)
        # '201709011234' not covered by dateparser
        result = re.match(r'[0-9]{8}', string)
        if result is not None:
            temp = result.group(0)
            candidate = '-'.join((temp[0:4], temp[4:6], temp[6:8]))
            if date_validator(candidate, '%Y-%m-%d') is True:
                return convert_date(candidate, '%Y-%m-%d', outputformat)

    # send to dateparser
    target = dateparser.parse(string, settings={'PREFER_DAY_OF_MONTH': 'first', 'PREFER_DATES_FROM': 'past', 'DATE_ORDER': 'DMY'})
    if target is not None:
        datestring = datetime.date.strftime(target, outputformat)
        if date_validator(datestring, outputformat) is True:
            return datestring
    return None


def examine_date_elements(tree, expression, outputformat):
    """Check HTML elements one by one for date expressions"""
    try:
        elements = tree.xpath(expression)
    except etree.XPathEvalError as err:
        logger.error('lxml expression %s throws an error: %s', expression, err)
    else:
        if elements is not None and len(elements) > 0:
            for elem in elements:
                # simple length heuristics
                textcontent = elem.text_content().strip()
                if 3 < len(textcontent) < 30 and re.search(r'\d', textcontent):
                    logger.debug('analyzing: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    attempt = try_ymd_date(elem.text_content().strip(), outputformat)
                    if attempt is not None:
                        logger.debug('result: %s', attempt)
                        if date_validator(attempt, outputformat) is True:
                            return attempt
    # catchall
    return None


def examine_header(tree, outputformat):
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
                    headerdate = try_ymd_date(elem.get('content'), outputformat)
                # modified: override published_time
                elif elem.get('property').lower() in ('article:modified_time', 'og:article:modified_time', 'og:updated_time'):
                    logger.debug('examining meta property: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    attempt = try_ymd_date(elem.get('content'), outputformat)
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
                    headerdate = try_ymd_date(elem.get('content'), outputformat)
            # other types # itemscope?
            elif 'itemprop' in elem.attrib:
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
            elif 'pubdate' in elem.attrib and headerdate is None:
                if elem.get('pubdate').lower() == 'pubdate':
                    logger.debug('examining meta pubdate: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    headerdate = try_ymd_date(elem.get('content'), outputformat)
            # http-equiv, rare http://www.standardista.com/html5/http-equiv-the-meta-attribute-explained/
            elif 'http-equiv' in elem.attrib:
                if elem.get('http-equiv').lower() in ('date', 'last-modified') and headerdate is None:
                    logger.debug('examining meta http-equiv: %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip())
                    headerdate = try_ymd_date(elem.get('content'), outputformat)
            #else:
            #    logger.debug('not found: %s %s', html.tostring(elem, pretty_print=False, encoding='unicode').strip(), elem.attrib)

    except etree.XPathEvalError as err:
        logger.error('XPath %s', err)
        return None

    if headerdate is not None and date_validator(headerdate, outputformat) is True:
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
        firstselect = occurrences.most_common(10)
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


def search_page(htmlstring, outputformat):
    """Search the page for common patterns (can lead to flawed results!)"""
    # init
    # pagedate = None

    # date ultimate rescue for the rest: most frequent year/month comination in the HTML
    ## this is risky

    ## 3 components
    # logger.debug('3 components')
    # target URL characteristics
    pattern = '/([0-9]{4}/[0-9]{2}/[0-9]{2})[01/]'
    catch = '([0-9]{4})/([0-9]{2})/([0-9]{2})'
    yearpat = '^\D?([12][0-9]{3})'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), bestmatch.group(3)])
        if date_validator(pagedate, '%Y-%m-%d') is True:
            logger.debug('date found for pattern "%s": %s', pattern, pagedate)
            return convert_date(pagedate, '%Y-%m-%d', outputformat)

    # more loosely structured data
    pattern = '\D([0-9]{4}[/.-][0-9]{2}[/.-][0-9]{2})\D'
    catch = '([0-9]{4})[/.-]([0-9]{2})[/.-]([0-9]{2})'
    yearpat = '^\D?([12][0-9]{3})'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), bestmatch.group(3)])
        if date_validator(pagedate, '%Y-%m-%d') is True:
            logger.debug('date found for pattern "%s": %s', pattern, pagedate)
            return convert_date(pagedate, '%Y-%m-%d', outputformat)
    #
    pattern = '\D([0-9]{2}[/.-][0-9]{2}[/.-][0-9]{4})\D'
    catch = '([0-9]{2})[/.-]([0-9]{2})[/.-]([0-9]{4})'
    yearpat = '(19[0-9]{2}|20[0-9]{2})\D?$'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(3), bestmatch.group(2), bestmatch.group(1)])
        if date_validator(pagedate, '%Y-%m-%d') is True:
            logger.debug('date found for pattern "%s": %s', pattern, pagedate)
            return convert_date(pagedate, '%Y-%m-%d', outputformat)

    # valid dates strings
    pattern = '(\D19[0-9]{2}[01][0-9][0-3][0-9]\D|\D20[0-9]{2}[01][0-9][0-3][0-9]\D)'
    catch = '([12][0-9]{3})([01][0-9])([0-3][0-9])'
    yearpat = '^\D?([12][0-9]{3})'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), bestmatch.group(3)])
        if date_validator(pagedate, '%Y-%m-%d') is True:
            logger.debug('date found for pattern "%s": %s', pattern, pagedate)
            return convert_date(pagedate, '%Y-%m-%d', outputformat)

    ## 2 components
    logger.debug('switching to two components')
    #
    pattern = '\D([0-9]{4}[/.-][0-9]{2})\D'
    catch = '([0-9]{4})[/.-]([0-9]{2})'
    yearpat = '^\D?([12][0-9]{3})'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), '01'])
        if date_validator(pagedate, '%Y-%m-%d') is True:
            logger.debug('date found for pattern "%s": %s', pattern, pagedate)
            return convert_date(pagedate, '%Y-%m-%d', outputformat)
    #
    pattern = '\D([0-9]{2}[/.-][0-9]{4})\D'
    catch = '([0-9]{2})[/.-]([0-9]{4})'
    yearpat = '([12][0-9]{3})\D?$'
    bestmatch = search_pattern(htmlstring, pattern, catch, yearpat)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(2), bestmatch.group(1), '01'])
        if date_validator(pagedate, '%Y-%m-%d') is True:
            logger.debug('date found for pattern "%s": %s', pattern, pagedate)
            return convert_date(pagedate, '%Y-%m-%d', outputformat)

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
        if date_validator(pagedate, '%Y-%m-%d') is True:
            logger.debug('date found for pattern "%s": %s', pattern, pagedate)
            return convert_date(pagedate, '%Y-%m-%d', outputformat)

    # catchall
    return None


def load_html(htmlobject):
    """Load object given as input and validate its type (accepted: LXML tree and string)"""
    if isinstance(htmlobject, html.HtmlElement):
        # copy tree
        tree = htmlobject
        # derive string
        htmlstring = html.tostring(htmlobject, encoding='unicode')
    elif isinstance(htmlobject, str):
        # robust parsing
        try:
            # copy string
            htmlstring = htmlobject
            # parse
            parser = html.HTMLParser() # encoding='utf8'
            tree = html.parse(StringIO(htmlobject), parser=parser)
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


def find_date(htmlobject, extensive_search=True, outputformat='%Y-%m-%d'):
    """Main function: apply a series of techniques to date the document, from safe to adventurous"""
    # init
    if output_format_validator(outputformat) is False:
        return
    tree, htmlstring = load_html(htmlobject)
    if tree is None:
        return

    # first, try header
    pagedate = examine_header(tree, outputformat)
    if pagedate is not None and date_validator(pagedate, outputformat) is True:
        return pagedate

    # <time>
    elements = tree.xpath('//time')
    if elements is not None and len(elements) > 0:
        for elem in elements:
            if 'datetime' in elem.attrib:
                logger.debug('time datetime found: %s', elem.get('datetime'))
                attempt = try_ymd_date(elem.get('datetime'), outputformat)
                if attempt is not None and date_validator(attempt, outputformat) is True:
                    return attempt # break
            # else:
            # ...

    # data-utime (mostly Facebook)
    elements = tree.xpath('//abbr[@data-utime]')
    if elements is not None and len(elements) > 0:
        reference = 0
        for elem in elements:
            try:
                candidate = int(elem.get('data-utime'))
            except ValueError:
                continue
            logger.debug('data-utime found: %s', candidate)
            # look for newest (i.e. largest time delta)
            if candidate > reference:
                reference = candidate
        # convert and return
        dateobject = datetime.datetime.fromtimestamp(reference)
        converted = dateobject.strftime(outputformat)
        return converted

    # expressions + text_content
    for expr in DATE_EXPRESSIONS:
        dateresult = examine_date_elements(tree, expr, outputformat)
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

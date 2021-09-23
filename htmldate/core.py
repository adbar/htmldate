# pylint:disable-msg=E0611,I1101
"""Module bundling all functions needed to determine the date of HTML strings
or LXML trees.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license

# standard
import logging
import re

from collections import Counter
from copy import deepcopy
from functools import lru_cache, partial
from lxml import etree, html

# own
from .extractors import (discard_unwanted, extract_url_date,
                         extract_partial_url_date, idiosyncrasies_search,
                         img_search, json_search, timestamp_search, try_ymd_date,
                         ADDITIONAL_EXPRESSIONS, DATE_EXPRESSIONS,
                         YEAR_PATTERN, YMD_PATTERN, COPYRIGHT_PATTERN,
                         THREE_PATTERN, THREE_CATCH,
                         THREE_LOOSE_PATTERN, THREE_LOOSE_CATCH,
                         SELECT_YMD_PATTERN, SELECT_YMD_YEAR, YMD_YEAR,
                         DATESTRINGS_PATTERN, DATESTRINGS_CATCH,
                         SLASHES_PATTERN, SLASHES_YEAR,
                         YYYYMM_PATTERN, YYYYMM_CATCH, MMYYYY_PATTERN,
                         MMYYYY_YEAR, SIMPLE_PATTERN)
from .settings import CACHE_SIZE, HTML_CLEANER, MAX_POSSIBLE_CANDIDATES
from .utils import load_html
from .validators import (check_extracted_reference, compare_values,
                         convert_date, date_validator, filter_ymd_candidate,
                         get_min_date, get_max_date, output_format_validator,
                         plausible_year_filter)


LOGGER = logging.getLogger(__name__)
def logstring(element):
    '''Format the element to be logged to a string.'''
    return html.tostring(element, pretty_print=False, encoding='unicode').strip()

DATE_ATTRIBUTES = {
                  'article.created', 'article_date_original',
                  'article.published', 'article:published_time', 
                  'bt:pubdate', 'citation_publication_date', 'created',
                  'cxenseparse:recs:publishtime', 'date', 'date_published',
                  'datecreated', 'dateposted', 'datepublished',
                  # Dublin Core: https://wiki.whatwg.org/wiki/MetaExtensions
                  'dc.date', 'dc.created', 'dc.date.created',
                  'dc.date.issued', 'dcterms.created', 'dcterms.date',
                  'dcterms.issued', 'dc:created', 'dc:date',
                  'gentime',
                  # Open Graph: https://opengraphprotocol.org/
                  'og:published_time', 'og:article:published_time',
                  'originalpublicationdate', 'parsely-pub-date',
                  'pubdate', 'publishdate', 'publish_date',
                  'published-date', 'publication_date',  'rnews:datepublished',
                  'sailthru.date', 'timestamp'
                  }
PROPERTY_MODIFIED = {
                    'article:modified_time', 'datemodified',
                    'dc.modified', 'dcterms.modified', 'modified_time',
                    'og:article:modified_time', 'og:updated_time',
                    'release_date', 'updated_time'
                    }


@lru_cache(maxsize=CACHE_SIZE)
def examine_date_elements(tree, expression, outputformat, extensive_search, min_date, max_date):
    """Check HTML elements one by one for date expressions"""
    try:
        elements = tree.xpath(expression)
    except etree.XPathEvalError as err:
        LOGGER.error('lxml expression %s throws an error: %s', expression, err)
        return None
    if not elements or len(elements) > MAX_POSSIBLE_CANDIDATES:
        return None
    # loop through the elements to analyze
    attempt = None
    for elem in elements:
        # trim
        textcontent = re.sub(r'[\n\r\s\t]+', ' ', elem.text_content(), re.MULTILINE).strip()
        # simple length heuristics
        if textcontent is not None and len(textcontent) > 6:
            # shorten and try the beginning of the string
            # trim non-digits at the end of the string
            toexamine = re.sub(r'\D+$', '', textcontent[:48])
            # more than 4 digits required # list(filter(str.isdigit, toexamine))
            #if len([c for c in toexamine if c.isdigit()]) < 4:
            #    continue
            LOGGER.debug('analyzing (HTML): %s', html.tostring(
                elem, pretty_print=False, encoding='unicode').translate(
                    {ord(c): None for c in '\n\t\r'}
                ).strip()[:100])
            attempt = try_ymd_date(toexamine, outputformat, extensive_search, min_date, max_date)
            if attempt is not None:
                break
        # try link title (Blogspot)
        title_attr = elem.get('title')
        if title_attr is not None and len(title_attr) > 0:
            toexamine = re.sub(r'\D+$', '', title_attr[:48])
            attempt = try_ymd_date(toexamine, outputformat, extensive_search, min_date, max_date)
            if attempt is not None:
                break
    # catchall
    return attempt


def examine_header(tree, outputformat, extensive_search, original_date, min_date, max_date):
    """
    Parse header elements to find date cues

    :param tree:
        LXML parsed tree object
    :type htmlstring: LXML tree
    :param outputformat:
        Provide a valid datetime format for the returned string
        (see datetime.strftime())
    :type outputformat: string
    :param extensive_search:
        Activate pattern-based opportunistic text search
    :type extensive_search: boolean
    :param original_date:
        Look for original date (e.g. publication date) instead of most recent
        one (e.g. last modified, updated time)
    :type original_date: boolean
    :param min_date:
        Set the earliest acceptable date manually (YYYY-MM-DD format)
    :type min_date: string
    :param max_date:
        Set the latest acceptable date manually (YYYY-MM-DD format)
    :type max_date: string
    :return: Returns a valid date expression as a string, or None

    """
    headerdate, reserve = None, None
    tryfunc = partial(try_ymd_date, outputformat=outputformat, extensive_search=extensive_search, min_date=min_date, max_date=max_date)
    # loop through all meta elements
    for elem in tree.iterfind('.//meta'):
        # safeguard
        if not elem.attrib: # len(elem.attrib) < 1:
            continue
        # property attribute
        if 'property' in elem.attrib and 'content' in elem.attrib:
            attribute = elem.get('property').lower()
            # original date
            if original_date is True:
                if attribute in DATE_ATTRIBUTES:
                    LOGGER.debug('examining meta property: %s', logstring(elem))
                    headerdate = tryfunc(elem.get('content'))
            # modified date: override published_time
            else:
                if attribute in PROPERTY_MODIFIED:
                    LOGGER.debug('examining meta property: %s', logstring(elem))
                    headerdate = tryfunc(elem.get('content'))
                elif attribute in DATE_ATTRIBUTES:
                    LOGGER.debug('examining meta property: %s', logstring(elem))
                    headerdate = tryfunc(elem.get('content'))
        # name attribute
        elif 'name' in elem.attrib and 'content' in elem.attrib:
            # url
            if elem.get('name').lower() == 'og:url':
                headerdate = extract_url_date(elem.get('content'), outputformat)
            # date
            elif elem.get('name').lower() in DATE_ATTRIBUTES:
                LOGGER.debug('examining meta name: %s', logstring(elem))
                headerdate = tryfunc(elem.get('content'))
            # modified
            elif elem.get('name').lower() in ('lastmodified', 'last-modified'):
                LOGGER.debug('examining meta name: %s', logstring(elem))
                if original_date is False:
                    headerdate = tryfunc(elem.get('content'))
                else:
                    reserve = tryfunc(elem.get('content'))
        elif 'pubdate' in elem.attrib:
            if elem.get('pubdate').lower() == 'pubdate':
                LOGGER.debug('examining meta pubdate: %s', logstring(elem))
                headerdate = tryfunc(elem.get('content'))
        # other types # itemscope?
        elif 'itemprop' in elem.attrib:
            attribute = elem.get('itemprop').lower()
            if attribute in (
                    'datecreated', 'datepublished', 'pubyear'
                ):
                LOGGER.debug('examining meta itemprop: %s', logstring(elem))
                if 'datetime' in elem.attrib:
                    headerdate = try_ymd_date(elem.get('datetime'), outputformat, extensive_search, min_date, max_date)
                elif 'content' in elem.attrib:
                    headerdate = tryfunc(elem.get('content'))
            # override
            elif attribute == 'datemodified' and original_date is False:
                LOGGER.debug('examining meta itemprop: %s', logstring(elem))
                if 'datetime' in elem.attrib:
                    headerdate = try_ymd_date(elem.get('datetime'), outputformat, extensive_search, min_date, max_date)
                elif 'content' in elem.attrib:
                    headerdate = tryfunc(elem.get('content'))
            # reserve with copyrightyear
            elif attribute == 'copyrightyear':
                LOGGER.debug('examining meta itemprop: %s', logstring(elem))
                if 'content' in elem.attrib:
                    attempt = '-'.join([elem.get('content'), '01', '01'])
                    if date_validator(attempt, '%Y-%m-%d', latest=max_date) is True:
                        reserve = attempt
        # http-equiv, rare http://www.standardista.com/html5/http-equiv-the-meta-attribute-explained/
        elif 'http-equiv' in elem.attrib:
            attribute = elem.get('http-equiv').lower()
            if attribute == 'date':
                LOGGER.debug('examining meta http-equiv: %s', logstring(elem))
                if original_date is True:
                    headerdate = tryfunc(elem.get('content'))
                else:
                    reserve = tryfunc(elem.get('content'))
            elif attribute == 'last-modified':
                LOGGER.debug('examining meta http-equiv: %s', logstring(elem))
                if original_date is False:
                    headerdate = tryfunc(elem.get('content'))
                else:
                    reserve = tryfunc(elem.get('content'))
        # exit loop
        if headerdate is not None:
            break
    # if nothing was found, look for lower granularity (so far: "copyright year")
    if headerdate is None and reserve is not None:
        LOGGER.debug('opting for reserve date with less granularity')
        headerdate = reserve
    # return value
    return headerdate


def select_candidate(occurrences, catch, yearpat, original_date, min_date, max_date):
    """Select a candidate among the most frequent matches"""
    match = None
    # LOGGER.debug('occurrences: %s', occurrences)
    if len(occurrences) == 0 or len(occurrences) > MAX_POSSIBLE_CANDIDATES:
        return None
    if len(occurrences) == 1:
        match = catch.search(list(occurrences.keys())[0])
        if match:
            return match
    # select among most frequent
    firstselect = occurrences.most_common(10)
    LOGGER.debug('firstselect: %s', firstselect)
    # sort and find probable candidates
    if original_date is False:
        bestones = sorted(firstselect, reverse=True)[:2]
    else:
        bestones = sorted(firstselect)[:2]
    first_pattern, first_count = bestones[0][0], bestones[0][1]
    second_pattern, second_count = bestones[1][0], bestones[1][1]
    LOGGER.debug('bestones: %s', bestones)
    # same number of occurrences: always take top of the pile
    if first_count == second_count:
        match = catch.search(first_pattern)
    else:
        year1 = int(yearpat.search(first_pattern).group(1))
        year2 = int(yearpat.search(second_pattern).group(1))
        # safety net: plausibility
        if date_validator(str(year1), '%Y', earliest=min_date, latest=max_date) is False:
            if date_validator(str(year2), '%Y', earliest=min_date, latest=max_date) is True:
                # LOGGER.debug('first candidate not suitable: %s', year1)
                match = catch.search(second_pattern)
            else:
                LOGGER.debug('no suitable candidate: %s %s', year1, year2)
                return None
        # safety net: newer date but up to 50% less frequent
        if year2 != year1 and second_count/first_count > 0.5:
            match = catch.search(second_pattern)
        # not newer or hopefully not significant
        else:
            match = catch.search(first_pattern)
    return match


def search_pattern(htmlstring, pattern, catch, yearpat, original_date, min_date, max_date):
    """Chained candidate filtering and selection"""
    candidates = plausible_year_filter(htmlstring, pattern, yearpat)
    return select_candidate(candidates, catch, yearpat, original_date, min_date, max_date)


def try_expression(expression, outputformat, extensive_search, min_date, max_date):
    '''Check if the text string could be a valid date expression'''
    # trim
    textcontent = re.sub(r'[\n\r\s\t]+', ' ', expression, re.MULTILINE).strip()
    # simple length heuristics list(filter(str.isdigit, textcontent))
    if not textcontent or len([c for c in textcontent if c.isdigit()]) < 4:
        return None
    # try the beginning of the string
    return try_ymd_date(textcontent[:48], outputformat, extensive_search, min_date, max_date)


@lru_cache(maxsize=CACHE_SIZE)
def compare_reference(reference, expression, outputformat, extensive_search, original_date, min_date, max_date):
    '''Compare candidate to current date reference (includes date validation and older/newer test)'''
    attempt = try_expression(expression, outputformat, extensive_search, min_date, max_date)
    if attempt is not None:
        new_reference = compare_values(reference, attempt, outputformat, original_date)
    else:
        new_reference = reference
    return new_reference


def examine_abbr_elements(tree, outputformat, extensive_search, original_date, min_date, max_date):
    '''Scan the page for abbr elements and check if their content contains an eligible date'''
    elements = tree.findall('.//abbr')
    if elements is not None and len(elements) < MAX_POSSIBLE_CANDIDATES:
        reference = 0
        for elem in elements:
            # data-utime (mostly Facebook)
            if 'data-utime' in elem.attrib:
                try:
                    candidate = int(elem.get('data-utime'))
                except ValueError:
                    continue
                LOGGER.debug('data-utime found: %s', candidate)
                # look for original date
                if original_date is True:
                    if reference == 0:
                        reference = candidate
                    elif candidate < reference:
                        reference = candidate
                # look for newest (i.e. largest time delta)
                else:
                    if candidate > reference:
                        reference = candidate
            # class
            if 'class' in elem.attrib:
                if elem.get('class') in ('published', 'date-published', 'time published'):
                    # other attributes
                    if 'title' in elem.attrib:
                        trytext = elem.get('title')
                        LOGGER.debug('abbr published-title found: %s', trytext)
                        # shortcut
                        if original_date is True:
                            attempt = try_ymd_date(trytext, outputformat, extensive_search, min_date, max_date)
                            if attempt is not None:
                                return attempt
                        else:
                            reference = compare_reference(reference, trytext, outputformat, extensive_search, original_date, min_date, max_date)
                            # faster execution
                            if reference > 0:
                                break
                    # dates, not times of the day
                    if elem.text and len(elem.text) > 10:
                        trytext = re.sub(r'^am ', '', elem.text)
                        LOGGER.debug('abbr published found: %s', trytext)
                        reference = compare_reference(reference, trytext, outputformat, extensive_search, original_date, min_date, max_date)
        # convert and return
        converted = check_extracted_reference(reference, outputformat, min_date, max_date)
        if converted is not None:
            return converted
        # try rescue in abbr content
        dateresult = examine_date_elements(tree, './/abbr', outputformat, extensive_search, min_date, max_date)
        if dateresult is not None:
            return dateresult
    return None


def examine_time_elements(tree, outputformat, extensive_search, original_date, min_date, max_date):
    '''Scan the page for time elements and check if their content contains an eligible date'''
    elements = tree.findall('.//time')
    if elements is not None and len(elements) < MAX_POSSIBLE_CANDIDATES:
        # scan all the tags and look for the newest one
        reference = 0
        for elem in elements:
            shortcut_flag = False
            # go for datetime
            if 'datetime' in elem.attrib and len(elem.get('datetime')) > 6:
                # shortcut: time pubdate
                if 'pubdate' in elem.attrib and elem.get('pubdate') == 'pubdate':
                    if original_date is True:
                        shortcut_flag = True
                    LOGGER.debug('time pubdate found: %s', elem.get('datetime'))
                # first choice: entry-date + datetime attribute
                elif 'class' in elem.attrib:
                    if elem.get('class').startswith('entry-date') or elem.get('class').startswith('entry-time'):
                        # shortcut
                        if original_date is True:
                            shortcut_flag = True
                        LOGGER.debug('time/datetime found: %s', elem.get('datetime'))
                    # updated time
                    elif elem.get('class') == 'updated' and original_date is False:
                        LOGGER.debug('updated time/datetime found: %s', elem.get('datetime'))
                # datetime attribute
                else:
                    LOGGER.debug('time/datetime found: %s', elem.get('datetime'))
                # analyze attribute
                if shortcut_flag is True:
                    attempt = try_ymd_date(elem.get('datetime'), outputformat, extensive_search, min_date, max_date)
                    if attempt is not None:
                        return attempt
                else:
                    reference = compare_reference(reference, elem.get('datetime'), outputformat, extensive_search, original_date, min_date, max_date)
                    if reference > 0:
                        break
            # bare text in element
            elif elem.text is not None and len(elem.text) > 6:
                LOGGER.debug('time/datetime found: %s', elem.text)
                reference = compare_reference(reference, elem.text, outputformat, extensive_search, original_date, min_date, max_date)
            # else...
        # return
        converted = check_extracted_reference(reference, outputformat, min_date, max_date)
        if converted is not None:
            return converted
    return None


def normalize_match(match):
    '''Normalize string output by adding "0" if necessary.'''
    if len(match.group(1)) == 1:
        day = '0' + match.group(1)
    else:
        day = match.group(1)
    if len(match.group(2)) == 1:
        month = '0' + match.group(2)
    else:
        month = match.group(2)
    return day, month


def search_page(htmlstring, outputformat, original_date, min_date, max_date):
    """
    Opportunistically search the HTML text for common text patterns

    :param htmlstring:
        The HTML document in string format, potentially cleaned and stripped to
        the core (much faster)
    :type htmlstring: string
    :param outputformat:
        Provide a valid datetime format for the returned string
        (see datetime.strftime())
    :type outputformat: string
    :param original_date:
        Look for original date (e.g. publication date) instead of most recent
        one (e.g. last modified, updated time)
    :type original_date: boolean
    :return: Returns a valid date expression as a string, or None

    """

    # copyright symbol
    LOGGER.debug('looking for copyright/footer information')
    copyear = 0
    bestmatch = search_pattern(htmlstring, COPYRIGHT_PATTERN, YEAR_PATTERN, YEAR_PATTERN, original_date, min_date, max_date)
    if bestmatch is not None:
        LOGGER.debug('Copyright detected: %s', bestmatch.group(0))
        if date_validator(bestmatch.group(0), '%Y', latest=max_date) is True:
            LOGGER.debug('copyright year/footer pattern found: %s', bestmatch.group(0))
            copyear = int(bestmatch.group(0))

    # 3 components
    LOGGER.debug('3 components')
    # target URL characteristics
    bestmatch = search_pattern(htmlstring, THREE_PATTERN, THREE_CATCH, YEAR_PATTERN, original_date, min_date, max_date)
    result = filter_ymd_candidate(bestmatch, THREE_PATTERN, original_date, copyear, outputformat, min_date, max_date)
    if result is not None:
        return result

    # more loosely structured data
    bestmatch = search_pattern(htmlstring, THREE_LOOSE_PATTERN, THREE_LOOSE_CATCH, YEAR_PATTERN, original_date, min_date, max_date)
    result = filter_ymd_candidate(bestmatch, THREE_LOOSE_PATTERN, original_date, copyear, outputformat, min_date, max_date)
    if result is not None:
        return result

    # YYYY-MM-DD/DD-MM-YYYY
    candidates = plausible_year_filter(htmlstring, SELECT_YMD_PATTERN, SELECT_YMD_YEAR)
    # revert DD-MM-YYYY patterns before sorting
    replacement = dict()
    for item in candidates:
        match = re.match(r'([0-3]?[0-9])[/.-]([01]?[0-9])[/.-]([0-9]{4})', item)
        day, month = normalize_match(match)
        candidate = '-'.join([match.group(3), month, day])
        replacement[candidate] = candidates[item]
    candidates = Counter(replacement)
    # select
    bestmatch = select_candidate(candidates, YMD_PATTERN, YMD_YEAR, original_date, min_date, max_date)
    result = filter_ymd_candidate(bestmatch, SELECT_YMD_PATTERN, original_date, copyear, outputformat, min_date, max_date)
    if result is not None:
        return result

    # valid dates strings
    bestmatch = search_pattern(htmlstring, DATESTRINGS_PATTERN, DATESTRINGS_CATCH, YEAR_PATTERN, original_date, min_date, max_date)
    result = filter_ymd_candidate(bestmatch, DATESTRINGS_PATTERN, original_date, copyear, outputformat, min_date, max_date)
    if result is not None:
        return result

    # DD?/MM?/YY
    candidates = plausible_year_filter(htmlstring, SLASHES_PATTERN, SLASHES_YEAR, tocomplete=True)
    # revert DD-MM-YYYY patterns before sorting
    replacement = dict()
    for item in candidates:
        match = re.match(r'([0-3]?[0-9])[/.]([01]?[0-9])[/.]([0-9]{2})', item)
        day, month = normalize_match(match)
        if match.group(3)[0] == '9':
            year = '19' + match.group(3)
        else:
            year = '20' + match.group(3)
        candidate = '-'.join([year, month, day])
        replacement[candidate] = candidates[item]
    candidates = Counter(replacement)
    bestmatch = select_candidate(candidates, YMD_PATTERN, YMD_YEAR, original_date, min_date, max_date)
    result = filter_ymd_candidate(bestmatch, SLASHES_PATTERN, original_date, copyear, outputformat, min_date, max_date)
    if result is not None:
        return result

    # 2 components
    LOGGER.debug('switching to two components')
    # first option
    bestmatch = search_pattern(htmlstring, YYYYMM_PATTERN, YYYYMM_CATCH, YEAR_PATTERN, original_date, min_date, max_date)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(1), bestmatch.group(2), '01'])
        if date_validator(pagedate, '%Y-%m-%d', latest=max_date) is True:
            if copyear == 0 or int(bestmatch.group(1)) >= copyear:
                LOGGER.debug('date found for pattern "%s": %s', YYYYMM_PATTERN, pagedate)
                return convert_date(pagedate, '%Y-%m-%d', outputformat)

    # 2 components, second option
    candidates = plausible_year_filter(htmlstring, MMYYYY_PATTERN, MMYYYY_YEAR, original_date)
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
    # select
    bestmatch = select_candidate(candidates, YMD_PATTERN, YMD_YEAR, original_date, min_date, max_date)
    result = filter_ymd_candidate(bestmatch, MMYYYY_PATTERN, original_date, copyear, outputformat, min_date, max_date)
    if result is not None:
        return result

    # catchall
    if copyear != 0:
        LOGGER.debug('using copyright year as default')
        return convert_date('-'.join([str(copyear), '01', '01']), '%Y-%m-%d', outputformat)

    # 1 component, last try
    LOGGER.debug('switching to one component')
    bestmatch = search_pattern(htmlstring, SIMPLE_PATTERN, YEAR_PATTERN, YEAR_PATTERN, original_date, min_date, max_date)
    if bestmatch is not None:
        pagedate = '-'.join([bestmatch.group(0), '01', '01'])
        if date_validator(pagedate, '%Y-%m-%d', latest=max_date) is True:
            if copyear == 0 or int(bestmatch.group(0)) >= copyear:
                LOGGER.debug('date found for pattern "%s": %s', SIMPLE_PATTERN, pagedate)
                return convert_date(pagedate, '%Y-%m-%d', outputformat)

    return None


def find_date(htmlobject, extensive_search=True, original_date=False, outputformat='%Y-%m-%d', url=None, verbose=False, min_date=None, max_date=None):
    """
    Extract dates from HTML documents using markup analysis and text patterns

    :param htmlobject:
        Two possibilities: 1. HTML document (e.g. body of HTTP request or .html-file) in text string
        form or LXML parsed tree or 2. URL string (gets detected automatically)
    :type htmlobject: string or lxml tree
    :param extensive_search:
        Activate pattern-based opportunistic text search
    :type extensive_search: boolean
    :param original_date:
        Look for original date (e.g. publication date) instead of most recent
        one (e.g. last modified, updated time)
    :type original_date: boolean
    :param outputformat:
        Provide a valid datetime format for the returned string
        (see datetime.strftime())
    :type outputformat: string
    :param url:
        Provide an URL manually for pattern-searching in URL
        (in some cases much faster)
    :type url: string
    :param verbose:
        Set verbosity level for debugging
    :type verbose: boolean
    :param min_date:
        Set the earliest acceptable date manually (YYYY-MM-DD format)
    :type min_date: string
    :param max_date:
        Set the latest acceptable date manually (YYYY-MM-DD format)
    :type max_date: string
    :return: Returns a valid date expression as a string, or None
    """

    # init
    if verbose is True:
        logging.basicConfig(level=logging.DEBUG)
    tree = load_html(htmlobject)
    find_date.extensive_search = extensive_search
    min_date, max_date = get_min_date(min_date), get_max_date(max_date)

    # safety
    if tree is None:
        return None
    if outputformat != '%Y-%m-%d' and output_format_validator(outputformat) is False:
        return None

    # URL
    if url is None:
        # link canonical
        for elem in tree.iterfind('.//link[@rel="canonical"]'):
            if 'href' in elem.attrib:
                url = elem.get('href')
                break
    if url is not None:
        dateresult = extract_url_date(url, outputformat)
        if dateresult is not None:
            return dateresult

    # first, try header
    try:
        header_result = examine_header(tree, outputformat, extensive_search,
                                       original_date, min_date, max_date)
    except etree.XPathEvalError as err:
        LOGGER.error('header XPath %s', err)
    else:
        if header_result is not None:
            return header_result

    # try to use JSON data
    json_result = json_search(tree, outputformat, original_date, min_date, max_date)
    if json_result is not None:
        return json_result

    # try abbr elements
    abbr_result = examine_abbr_elements(
        tree, outputformat, extensive_search, original_date, min_date, max_date
    )
    if abbr_result is not None:
        return abbr_result

    # expressions + text_content
    # first try in pruned tree
    search_tree, discarded = discard_unwanted(deepcopy(tree))
    dateresult = examine_date_elements(search_tree, DATE_EXPRESSIONS,
        outputformat, extensive_search, min_date, max_date)
    if dateresult is not None:
        return dateresult
    # supply more expressions (other languages)
    if extensive_search is True:
        dateresult = examine_date_elements(search_tree, ADDITIONAL_EXPRESSIONS,
            outputformat, extensive_search, min_date, max_date)
        if dateresult is not None:
            return dateresult

    # search in discarded parts (currently: footers and archive.org-banner)
    for subtree in discarded:
        dateresult = examine_date_elements(subtree, DATE_EXPRESSIONS,
            outputformat, extensive_search, min_date, max_date)
        if dateresult is not None:
            return dateresult

    # try time elements
    time_result = examine_time_elements(
        search_tree, outputformat, extensive_search, original_date, min_date, max_date
    )
    if time_result is not None:
        return time_result

    # clean before string search
    try:
        cleaned_html = HTML_CLEANER.clean_html(deepcopy(tree))
    # rare LXML error: no NULL bytes or control characters
    except ValueError:
        cleaned_html = tree
    # robust conversion to string
    try:
        htmlstring = html.tostring(cleaned_html, pretty_print=False, encoding='unicode')
    except UnicodeDecodeError:
        htmlstring = html.tostring(cleaned_html, pretty_print=False).decode('utf-8', 'ignore')
    # remove comments by hand as faulty in lxml?
    # htmlstring = re.sub(r'<!--.+?-->', '', htmlstring, flags=re.DOTALL)

    # date regex timestamp rescue
    timestamp_result = timestamp_search(htmlstring, outputformat, min_date, max_date)
    if timestamp_result is not None:
        return timestamp_result

    # precise patterns and idiosyncrasies
    text_result = idiosyncrasies_search(htmlstring, outputformat, min_date, max_date)
    if text_result is not None:
        return text_result

    # title
    for title_elem in tree.iter('title', 'h1'):
        attempt = try_ymd_date(title_elem.text_content(), outputformat, extensive_search, min_date, max_date)
        if attempt is not None:
            return attempt

    # last try: URL 2
    if url is not None:
        dateresult = extract_partial_url_date(url, outputformat)
        if dateresult is not None:
            return dateresult

    # try image elements
    img_result = img_search(
        tree, outputformat, min_date, max_date
        )
    if img_result is not None:
        return img_result

    # last resort
    if extensive_search is True:
        LOGGER.debug('extensive search started')
        # div and p elements?
        # TODO: check all and decide according to original_date
        reference = 0
        for textpart in [t for t in cleaned_html.xpath('.//div/text()|.//p/text()') if 0 < len(t) < 80]:
            reference = compare_reference(reference, textpart, outputformat, extensive_search, original_date, min_date, max_date)
        # return
        converted = check_extracted_reference(reference, outputformat, min_date, max_date)
        if converted is not None:
            return converted
        # search page HTML
        return search_page(htmlstring, outputformat, original_date, min_date, max_date)

    return None

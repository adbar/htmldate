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
from datetime import datetime
from functools import lru_cache, partial
from typing import Match, Optional, Pattern, Tuple, Union, Counter as Counter_Type

from lxml.html import HtmlElement, tostring  # type: ignore

# own
from .extractors import (
    discard_unwanted,
    extract_url_date,
    extract_partial_url_date,
    idiosyncrasies_search,
    img_search,
    json_search,
    regex_parse,
    timestamp_search,
    try_date_expr,
    DATE_EXPRESSIONS,
    FAST_PREPEND,
    SLOW_PREPEND,
    FREE_TEXT_EXPRESSIONS,
    MAX_TEXT_SIZE,
    YEAR_PATTERN,
    YMD_PATTERN,
    COPYRIGHT_PATTERN,
    THREE_PATTERN,
    THREE_CATCH,
    THREE_LOOSE_PATTERN,
    THREE_LOOSE_CATCH,
    SELECT_YMD_PATTERN,
    SELECT_YMD_YEAR,
    YMD_YEAR,
    DATESTRINGS_PATTERN,
    DATESTRINGS_CATCH,
    SLASHES_PATTERN,
    SLASHES_YEAR,
    YYYYMM_PATTERN,
    YYYYMM_CATCH,
    MMYYYY_PATTERN,
    MMYYYY_YEAR,
    SIMPLE_PATTERN,
    THREE_COMP_REGEX_A,
    THREE_COMP_REGEX_B,
    TWO_COMP_REGEX,
)
from .settings import CACHE_SIZE, HTML_CLEANER, MAX_POSSIBLE_CANDIDATES
from .utils import load_html
from .validators import (
    check_extracted_reference,
    compare_values,
    convert_date,
    date_validator,
    filter_ymd_candidate,
    get_min_date,
    get_max_date,
    output_format_validator,
    plausible_year_filter,
)


LOGGER = logging.getLogger(__name__)


def logstring(element: HtmlElement) -> str:
    """Format the element to be logged to a string."""
    return tostring(element, pretty_print=False, encoding="unicode").strip()  # type: ignore


DATE_ATTRIBUTES = {
    "analyticsattributes.articledate",
    "article.created",
    "article_date_original",
    "article:post_date",
    "article.published",
    "article:published",
    "article:published_date",
    "article:published_time",
    "article:publicationdate",
    "bt:pubdate",
    "citation_date",
    "citation_publication_date",
    "content_create_date",
    "created",
    "cxenseparse:recs:publishtime",
    "date",
    "date_created",
    "date_published",
    "datecreated",
    "dateposted",
    "datepublished",
    # Dublin Core: https://wiki.whatwg.org/wiki/MetaExtensions
    "dc.date",
    "dc.created",
    "dc.date.created",
    "dc.date.issued",
    "dc.date.publication",
    "dcsext.articlefirstpublished",
    "dcterms.created",
    "dcterms.date",
    "dcterms.issued",
    "dc:created",
    "dc:date",
    "displaydate",
    "doc_date",
    "field-name-post-date",
    "gentime",
    "mediator_published_time",
    "meta",  # too loose?
    # Open Graph: https://opengraphprotocol.org/
    "og:article:published",
    "og:article:published_time",
    "og:datepublished",
    "og:pubdate",
    "og:publish_date",
    "og:published_time",
    "og:question:published_time",
    "originalpublicationdate",
    "parsely-pub-date",
    "pdate",
    "ptime",
    "pubdate",
    "publishdate",
    "publish_date",
    "publish_time",
    "publish-date",
    "published-date",
    "published_date",
    "published_time",
    "publisheddate",
    "publication_date",
    "rbpubdate",
    "release_date",
    "rnews:datepublished",
    "sailthru.date",
    "shareaholic:article_published_time",
    "timestamp",
    "twt-published-at",
    "video:release_date",
    "vr:published_time",
}


NAME_MODIFIED = {
    "lastdate",
    "lastmod",
    "lastmodified",
    "last-modified",
    "modified",
    "utime",
}


PROPERTY_MODIFIED = {
    "article:modified",
    "article:modified_date",
    "article:modified_time",
    "article:post_modified",
    "bt:moddate",
    "datemodified",
    "dc.modified",
    "dcterms.modified",
    "lastmodified",
    "modified_time",
    "modificationdate",
    "og:article:modified_time",
    "og:modified_time",
    "og:updated_time",
    "release_date",
    "revision_date",
    "updated_time",
}


ITEMPROP_ATTRS_ORIGINAL = {"datecreated", "datepublished", "pubyear"}
ITEMPROP_ATTRS_MODIFIED = {"datemodified", "dateupdate"}
ITEMPROP_ATTRS = ITEMPROP_ATTRS_ORIGINAL.union(ITEMPROP_ATTRS_MODIFIED)
CLASS_ATTRS = {"date-published", "published", "time published"}

NON_DIGITS_REGEX = re.compile(r"\D+$")


def examine_date_elements(
    tree: HtmlElement,
    expression: str,
    outputformat: str,
    extensive_search: bool,
    min_date: datetime,
    max_date: datetime,
) -> Optional[str]:
    """Check HTML elements one by one for date expressions"""
    elements = tree.xpath(expression)
    if not elements or len(elements) > MAX_POSSIBLE_CANDIDATES:
        return None
    # loop through the elements to analyze
    attempt = None
    for elem in elements:
        # trim
        text = elem.text_content().strip()
        # simple length heuristic
        if len(text) > 6:  # could be 8 or 9
            # shorten and try the beginning of the string
            # trim non-digits at the end of the string
            text = NON_DIGITS_REGEX.sub("", text[:MAX_TEXT_SIZE])
            LOGGER.debug(
                "analyzing (HTML): %s",
                " ".join(logstring(elem).split())[:100],
            )
            attempt = try_date_expr(
                text, outputformat, extensive_search, min_date, max_date
            )
            if attempt is not None:
                break
        # try link title (Blogspot)
        title_attr = elem.get("title", "").strip()
        if title_attr is not None and len(title_attr) > 0:
            title_attr = NON_DIGITS_REGEX.sub("", title_attr[:MAX_TEXT_SIZE])
            attempt = try_date_expr(
                title_attr, outputformat, extensive_search, min_date, max_date
            )
            if attempt is not None:
                break
    # catchall
    return attempt


def examine_header(
    tree: HtmlElement,
    outputformat: str,
    extensive_search: bool,
    original_date: bool,
    min_date: datetime,
    max_date: datetime,
) -> Optional[str]:
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
        Set the earliest acceptable date manually (ISO 8601 YMD format)
    :type min_date: datetime
    :param max_date:
        Set the latest acceptable date manually (ISO 8601 YMD format)
    :type max_date: datetime
    :return: Returns a valid date expression as a string, or None

    """
    headerdate, reserve = None, None
    tryfunc = partial(
        try_date_expr,
        outputformat=outputformat,
        extensive_search=extensive_search,
        min_date=min_date,
        max_date=max_date,
    )
    # loop through all meta elements
    for elem in tree.iterfind(".//meta"):
        # safeguard
        if not elem.attrib or (
            not "content" in elem.attrib and not "datetime" in elem.attrib
        ):
            continue
        # name attribute, most frequent
        if "name" in elem.attrib:
            attribute = elem.get("name").lower()
            # url
            if attribute == "og:url":
                reserve = extract_url_date(
                    elem.get("content"), outputformat, min_date, max_date
                )
            # date
            elif attribute in DATE_ATTRIBUTES:
                LOGGER.debug("examining meta name: %s", logstring(elem))
                headerdate = tryfunc(elem.get("content"))
            # modified
            elif attribute in NAME_MODIFIED:
                LOGGER.debug("examining meta name: %s", logstring(elem))
                if not original_date:
                    headerdate = tryfunc(elem.get("content"))
                else:
                    reserve = tryfunc(elem.get("content"))
        # property attribute
        elif "property" in elem.attrib:
            attribute = elem.get("property").lower()
            # original date or modified date: override published_time
            if (original_date and attribute in DATE_ATTRIBUTES) or (
                not original_date
                and (attribute in PROPERTY_MODIFIED or attribute in DATE_ATTRIBUTES)
            ):
                LOGGER.debug("examining meta property: %s", logstring(elem))
                headerdate = tryfunc(elem.get("content"))
        # itemprop
        elif "itemprop" in elem.attrib:
            attribute = elem.get("itemprop").lower()
            # original: store / updated: override date
            if attribute in ITEMPROP_ATTRS:
                LOGGER.debug("examining meta itemprop: %s", logstring(elem))
                attempt = tryfunc(elem.get("datetime") or elem.get("content"))
                # store value
                if attempt is not None:
                    if (attribute in ITEMPROP_ATTRS_ORIGINAL and original_date) or (
                        attribute in ITEMPROP_ATTRS_MODIFIED and not original_date
                    ):
                        headerdate = attempt
                    # put on hold: hurts precision
                    # else:
                    #    reserve = attempt
            # reserve with copyrightyear
            elif attribute == "copyrightyear":
                LOGGER.debug("examining meta itemprop: %s", logstring(elem))
                if "content" in elem.attrib:
                    attempt = "-".join([elem.get("content"), "01", "01"])
                    if (
                        date_validator(
                            attempt, "%Y-%m-%d", earliest=min_date, latest=max_date
                        )
                        is True
                    ):
                        reserve = attempt
        # pubdate, relatively rare
        elif "pubdate" in elem.attrib:
            if elem.get("pubdate").lower() == "pubdate":
                LOGGER.debug("examining meta pubdate: %s", logstring(elem))
                headerdate = tryfunc(elem.get("content"))
        # http-equiv, rare
        elif "http-equiv" in elem.attrib:
            attribute = elem.get("http-equiv").lower()
            if attribute == "date":
                LOGGER.debug("examining meta http-equiv: %s", logstring(elem))
                if original_date:
                    headerdate = tryfunc(elem.get("content"))
                else:
                    reserve = tryfunc(elem.get("content"))
            elif attribute == "last-modified":
                LOGGER.debug("examining meta http-equiv: %s", logstring(elem))
                if not original_date:
                    headerdate = tryfunc(elem.get("content"))
                else:
                    reserve = tryfunc(elem.get("content"))
        # exit loop
        if headerdate is not None:
            break
    # if nothing was found, look for lower granularity (so far: "copyright year")
    if headerdate is None and reserve is not None:
        LOGGER.debug("opting for reserve date with less granularity")
        headerdate = reserve
    # return value
    return headerdate


def select_candidate(
    occurrences: Counter_Type[str],
    catch: Pattern[str],
    yearpat: Pattern[str],
    original_date: bool,
    min_date: datetime,
    max_date: datetime,
) -> Optional[Match[str]]:
    """Select a candidate among the most frequent matches"""
    match, year1, year2 = None, None, None
    # LOGGER.debug('occurrences: %s', occurrences)
    if len(occurrences) == 0 or len(occurrences) > MAX_POSSIBLE_CANDIDATES:
        return None
    if len(occurrences) == 1:
        match = catch.search(list(occurrences.keys())[0])
        if match:
            return match
    # select among most frequent
    firstselect = occurrences.most_common(10)
    LOGGER.debug("firstselect: %s", firstselect)
    # sort and find probable candidates
    if original_date:
        bestones = sorted(firstselect)[:2]
    else:
        bestones = sorted(firstselect, reverse=True)[:2]

    first_pattern, first_count = bestones[0][0], bestones[0][1]
    second_pattern, second_count = bestones[1][0], bestones[1][1]
    LOGGER.debug("bestones: %s", bestones)
    # plausibility heuristics
    validation1, validation2 = False, False
    match1 = yearpat.search(first_pattern)
    if match1 is not None:
        year1 = match1[1]
        validation1 = date_validator(year1, "%Y", earliest=min_date, latest=max_date)
    match2 = yearpat.search(second_pattern)
    if match2 is not None:
        year2 = match2[1]
        validation2 = date_validator(year2, "%Y", earliest=min_date, latest=max_date)
    # safety net: plausibility
    if validation1 is True and validation2 is True:
        # same number of occurrences: always take top of the pile?
        if first_count == second_count:
            match = catch.search(first_pattern)
        # safety net: newer date but up to 50% less frequent
        elif year2 != year1 and second_count / first_count > 0.5:
            match = catch.search(second_pattern)
        # not newer or hopefully not significant
        else:
            match = catch.search(first_pattern)
    elif validation1 is False and validation2 is True:
        match = catch.search(second_pattern)
    elif validation1 is True and validation2 is False:
        match = catch.search(first_pattern)
    else:
        LOGGER.debug("no suitable candidate: %s %s", year1, year2)
        return None
    return match


def search_pattern(
    htmlstring: str,
    pattern: Pattern[str],
    catch: Pattern[str],
    yearpat: Pattern[str],
    original_date: bool,
    min_date: datetime,
    max_date: datetime,
) -> Optional[Match[str]]:
    """Chained candidate filtering and selection"""
    candidates = plausible_year_filter(
        htmlstring, pattern=pattern, yearpat=yearpat, earliest=min_date, latest=max_date
    )
    return select_candidate(
        candidates, catch, yearpat, original_date, min_date, max_date
    )


@lru_cache(maxsize=CACHE_SIZE)
def compare_reference(
    reference: int,
    expression: str,
    outputformat: str,
    extensive_search: bool,
    original_date: bool,
    min_date: datetime,
    max_date: datetime,
) -> int:
    """Compare candidate to current date reference (includes date validation and older/newer test)"""
    attempt = try_date_expr(
        expression, outputformat, extensive_search, min_date, max_date
    )
    if attempt is not None:
        return compare_values(reference, attempt, outputformat, original_date)
    return reference


def examine_abbr_elements(
    tree: HtmlElement,
    outputformat: str,
    extensive_search: bool,
    original_date: bool,
    min_date: datetime,
    max_date: datetime,
) -> Optional[str]:
    """Scan the page for abbr elements and check if their content contains an eligible date"""
    elements = tree.findall(".//abbr")
    if elements is not None and len(elements) < MAX_POSSIBLE_CANDIDATES:
        reference = 0
        for elem in elements:
            # data-utime (mostly Facebook)
            if "data-utime" in elem.attrib:
                try:
                    candidate = int(elem.get("data-utime"))
                except ValueError:
                    continue
                LOGGER.debug("data-utime found: %s", candidate)
                # look for original date
                if original_date and (reference == 0 or candidate < reference):
                    reference = candidate
                # look for newest (i.e. largest time delta)
                elif not original_date and candidate > reference:
                    reference = candidate
            # class
            elif elem.get("class") in CLASS_ATTRS:
                # other attributes
                if "title" in elem.attrib:
                    trytext = elem.get("title")
                    LOGGER.debug("abbr published-title found: %s", trytext)
                    # shortcut
                    if original_date:
                        attempt = try_date_expr(
                            trytext, outputformat, extensive_search, min_date, max_date
                        )
                        if attempt is not None:
                            return attempt
                    else:
                        reference = compare_reference(
                            reference,
                            trytext,
                            outputformat,
                            extensive_search,
                            original_date,
                            min_date,
                            max_date,
                        )
                        # faster execution
                        if reference > 0:
                            break
                # dates, not times of the day
                elif elem.text and len(elem.text) > 10:
                    LOGGER.debug("abbr published found: %s", elem.text)
                    reference = compare_reference(
                        reference,
                        elem.text,
                        outputformat,
                        extensive_search,
                        original_date,
                        min_date,
                        max_date,
                    )
        # convert and return
        converted = check_extracted_reference(
            reference, outputformat, min_date, max_date
        )
        if converted is not None:
            return converted
        # try rescue in abbr content
        dateresult = examine_date_elements(
            tree, ".//abbr", outputformat, extensive_search, min_date, max_date
        )
        if dateresult is not None:
            return dateresult
    return None


def examine_time_elements(
    tree: HtmlElement,
    outputformat: str,
    extensive_search: bool,
    original_date: bool,
    min_date: datetime,
    max_date: datetime,
) -> Optional[str]:
    """Scan the page for time elements and check if their content contains an eligible date"""
    elements = tree.findall(".//time")
    if elements is not None and len(elements) < MAX_POSSIBLE_CANDIDATES:
        # scan all the tags and look for the newest one
        reference = 0
        for elem in elements:
            shortcut_flag = False
            # go for datetime
            if "datetime" in elem.attrib and len(elem.get("datetime")) > 6:
                # shortcut: time pubdate
                if (
                    "pubdate" in elem.attrib
                    and elem.get("pubdate") == "pubdate"
                    and original_date
                ):
                    shortcut_flag = True
                    LOGGER.debug(
                        "shortcut for time pubdate found: %s", elem.get("datetime")
                    )
                # shortcuts: class attribute
                elif "class" in elem.attrib:
                    if original_date and (
                        elem.get("class").startswith("entry-date")
                        or elem.get("class").startswith("entry-time")
                    ):
                        shortcut_flag = True
                        LOGGER.debug(
                            "shortcut for time/datetime found: %s", elem.get("datetime")
                        )
                    # updated time
                    elif not original_date and elem.get("class") == "updated":
                        shortcut_flag = True
                        LOGGER.debug(
                            "shortcut for updated time/datetime found: %s",
                            elem.get("datetime"),
                        )
                # datetime attribute
                else:
                    LOGGER.debug("time/datetime found: %s", elem.get("datetime"))
                # analyze attribute
                if shortcut_flag:
                    attempt = try_date_expr(
                        elem.get("datetime"),
                        outputformat,
                        extensive_search,
                        min_date,
                        max_date,
                    )
                    if attempt is not None:
                        return attempt
                else:
                    reference = compare_reference(
                        reference,
                        elem.get("datetime"),
                        outputformat,
                        extensive_search,
                        original_date,
                        min_date,
                        max_date,
                    )
            # bare text in element
            elif elem.text is not None and len(elem.text) > 6:
                LOGGER.debug("time/datetime found in text: %s", elem.text)
                reference = compare_reference(
                    reference,
                    elem.text,
                    outputformat,
                    extensive_search,
                    original_date,
                    min_date,
                    max_date,
                )
            # else...?
        # return
        converted = check_extracted_reference(
            reference, outputformat, min_date, max_date
        )
        if converted is not None:
            return converted
    return None


def normalize_match(match: Optional[Match[str]]) -> Tuple[str, str]:
    """Normalize string output by adding "0" if necessary."""
    day = match[1]  # type: ignore[index]
    if len(day) == 1:
        day = "0" + day
    month = match[2]  # type: ignore[index]
    if len(month) == 1:
        month = "0" + month
    return day, month


def search_page(
    htmlstring: str,
    outputformat: str,
    original_date: bool,
    min_date: datetime,
    max_date: datetime,
) -> Optional[str]:
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
    :param min_date:
        Set the earliest acceptable date manually (ISO 8601 YMD format)
    :type min_date: datetime
    :param max_date:
        Set the latest acceptable date manually (ISO 8601 YMD format)
    :type max_date: datetime
    :return: Returns a valid date expression as a string, or None

    """

    # copyright symbol
    LOGGER.debug("looking for copyright/footer information")
    copyear = 0
    bestmatch = search_pattern(
        htmlstring,
        COPYRIGHT_PATTERN,
        YEAR_PATTERN,
        YEAR_PATTERN,
        original_date,
        min_date,
        max_date,
    )
    if bestmatch is not None:
        LOGGER.debug("Copyright detected: %s", bestmatch[0])
        if (
            date_validator(bestmatch[0], "%Y", earliest=min_date, latest=max_date)
            is True
        ):
            LOGGER.debug("copyright year/footer pattern found: %s", bestmatch[0])
            copyear = int(bestmatch[0])

    # 3 components
    LOGGER.debug("3 components")
    # target URL characteristics
    bestmatch = search_pattern(
        htmlstring,
        THREE_PATTERN,
        THREE_CATCH,
        YEAR_PATTERN,
        original_date,
        min_date,
        max_date,
    )
    result = filter_ymd_candidate(
        bestmatch,
        THREE_PATTERN,
        original_date,
        copyear,
        outputformat,
        min_date,
        max_date,
    )
    if result is not None:
        return result

    # more loosely structured data
    bestmatch = search_pattern(
        htmlstring,
        THREE_LOOSE_PATTERN,
        THREE_LOOSE_CATCH,
        YEAR_PATTERN,
        original_date,
        min_date,
        max_date,
    )
    result = filter_ymd_candidate(
        bestmatch,
        THREE_LOOSE_PATTERN,
        original_date,
        copyear,
        outputformat,
        min_date,
        max_date,
    )
    if result is not None:
        return result

    # YYYY-MM-DD/DD-MM-YYYY
    candidates = plausible_year_filter(
        htmlstring,
        pattern=SELECT_YMD_PATTERN,
        yearpat=SELECT_YMD_YEAR,
        earliest=min_date,
        latest=max_date,
    )
    # revert DD-MM-YYYY patterns before sorting
    replacement = {}
    for item in candidates:
        match = THREE_COMP_REGEX_A.match(item)
        day, month = normalize_match(match)
        candidate = "-".join([match[3], month, day])  # type: ignore[index]
        replacement[candidate] = candidates[item]
    candidates = Counter(replacement)
    # select
    bestmatch = select_candidate(
        candidates, YMD_PATTERN, YMD_YEAR, original_date, min_date, max_date
    )
    result = filter_ymd_candidate(
        bestmatch,
        SELECT_YMD_PATTERN,
        original_date,
        copyear,
        outputformat,
        min_date,
        max_date,
    )
    if result is not None:
        return result

    # valid dates strings
    bestmatch = search_pattern(
        htmlstring,
        DATESTRINGS_PATTERN,
        DATESTRINGS_CATCH,
        YEAR_PATTERN,
        original_date,
        min_date,
        max_date,
    )
    result = filter_ymd_candidate(
        bestmatch,
        DATESTRINGS_PATTERN,
        original_date,
        copyear,
        outputformat,
        min_date,
        max_date,
    )
    if result is not None:
        return result

    # DD?/MM?/YY
    candidates = plausible_year_filter(
        htmlstring,
        pattern=SLASHES_PATTERN,
        yearpat=SLASHES_YEAR,
        earliest=min_date,
        latest=max_date,
        incomplete=True,
    )
    # revert DD-MM-YYYY patterns before sorting
    replacement = {}
    for item in candidates:
        match = THREE_COMP_REGEX_B.match(item)
        day, month = normalize_match(match)
        if match[3][0] == "9":  # type: ignore[index]
            year = "19" + match[3]  # type: ignore[index]
        else:
            year = "20" + match[3]  # type: ignore[index]
        candidate = "-".join([year, month, day])
        replacement[candidate] = candidates[item]
    candidates = Counter(replacement)
    bestmatch = select_candidate(
        candidates, YMD_PATTERN, YMD_YEAR, original_date, min_date, max_date
    )
    result = filter_ymd_candidate(
        bestmatch,
        SLASHES_PATTERN,
        original_date,
        copyear,
        outputformat,
        min_date,
        max_date,
    )
    if result is not None:
        return result

    # 2 components
    LOGGER.debug("switching to two components")
    # first option
    bestmatch = search_pattern(
        htmlstring,
        YYYYMM_PATTERN,
        YYYYMM_CATCH,
        YEAR_PATTERN,
        original_date,
        min_date,
        max_date,
    )
    if bestmatch is not None:
        pagedate = "-".join([bestmatch[1], bestmatch[2], "01"])
        if date_validator(
            pagedate, "%Y-%m-%d", earliest=min_date, latest=max_date
        ) is True and (copyear == 0 or int(bestmatch[1]) >= copyear):
            LOGGER.debug('date found for pattern "%s": %s', YYYYMM_PATTERN, pagedate)
            return convert_date(pagedate, "%Y-%m-%d", outputformat)

    # 2 components, second option
    candidates = plausible_year_filter(
        htmlstring,
        pattern=MMYYYY_PATTERN,
        yearpat=MMYYYY_YEAR,
        earliest=min_date,
        latest=max_date,
        incomplete=original_date,
    )
    # revert DD-MM-YYYY patterns before sorting
    replacement = {}
    for item in candidates:
        match = TWO_COMP_REGEX.match(item)
        month = match[1]  # type: ignore[index]
        if len(month) == 1:
            month = "0" + month
        candidate = "-".join([match[2], month, "01"])  # type: ignore[index]
        replacement[candidate] = candidates[item]
    candidates = Counter(replacement)
    # select
    bestmatch = select_candidate(
        candidates, YMD_PATTERN, YMD_YEAR, original_date, min_date, max_date
    )
    result = filter_ymd_candidate(
        bestmatch,
        MMYYYY_PATTERN,
        original_date,
        copyear,
        outputformat,
        min_date,
        max_date,
    )
    if result is not None:
        return result

    # try full-blown text regex on all HTML?
    dateobject = regex_parse(htmlstring)
    # todo: find all candidates and disambiguate?
    if date_validator(
        dateobject, outputformat, earliest=min_date, latest=max_date
    ) is True and (
        copyear == 0 or dateobject.year >= copyear  # type: ignore[union-attr]
    ):
        try:
            LOGGER.debug("regex result on HTML: %s", dateobject)
            return dateobject.strftime(outputformat)  # type: ignore
        except ValueError as err:
            LOGGER.error("value error during conversion: %s %s", dateobject, err)

    # catchall: copyright mention
    if copyear != 0:
        LOGGER.debug("using copyright year as default")
        return convert_date(
            "-".join([str(copyear), "01", "01"]), "%Y-%m-%d", outputformat
        )

    # last resort: 1 component
    LOGGER.debug("switching to one component")
    bestmatch = search_pattern(
        htmlstring,
        SIMPLE_PATTERN,
        YEAR_PATTERN,
        YEAR_PATTERN,
        original_date,
        min_date,
        max_date,
    )
    if bestmatch is not None:
        pagedate = "-".join([bestmatch[0], "01", "01"])
        if (
            date_validator(pagedate, "%Y-%m-%d", earliest=min_date, latest=max_date)
            is True
            and int(bestmatch[0]) >= copyear
        ):
            LOGGER.debug('date found for pattern "%s": %s', SIMPLE_PATTERN, pagedate)
            return convert_date(pagedate, "%Y-%m-%d", outputformat)

    return None


def find_date(
    htmlobject: HtmlElement,
    extensive_search: bool = True,
    original_date: bool = False,
    outputformat: str = "%Y-%m-%d",
    url: Optional[str] = None,
    verbose: bool = False,
    min_date: Optional[Union[datetime, str]] = None,
    max_date: Optional[Union[datetime, str]] = None,
    deferred_url_extractor: bool = False,
) -> Optional[str]:
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
        Set the earliest acceptable date manually (ISO 8601 YMD format)
    :type min_date: datetime, string
    :param max_date:
        Set the latest acceptable date manually (ISO 8601 YMD format)
    :type max_date: datetime, string
    :param deferred_url_extractor:
        Use url extractor as backup only to prioritize full expressions,
        e.g. of the type `%Y-%m-%d %H:%M:%S`
    :type deferred_url_extractor: boolean
    :return: Returns a valid date expression as a string, or None
    """

    # init
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    tree = load_html(htmlobject)

    # safeguards
    if tree is None:
        return None
    if outputformat != "%Y-%m-%d" and not output_format_validator(outputformat):
        return None

    # define time boundaries
    min_date, max_date = get_min_date(min_date), get_max_date(max_date)
    # unclear what this line is for and it impedes type checking:
    # find_date.extensive_search = extensive_search

    # URL
    url_result = None
    if url is None:
        # probe for canonical links
        urlelem = tree.find('.//link[@rel="canonical"]')
        if urlelem is not None:
            url = urlelem.get("href")

    # direct processing of URL info
    if url is not None:
        url_result = extract_url_date(url, outputformat, min_date, max_date)
        if url_result is not None and not deferred_url_extractor:
            return url_result

    # first, try header
    header_result = examine_header(
        tree, outputformat, extensive_search, original_date, min_date, max_date
    )
    if header_result is not None:
        return header_result

    # try to use JSON data
    json_result = json_search(tree, outputformat, original_date, min_date, max_date)
    if json_result is not None:
        return json_result

    # deferred processing of URL info (may be moved even further down if necessary)
    if deferred_url_extractor and url_result is not None:
        return url_result

    # try abbr elements
    abbr_result = examine_abbr_elements(
        tree, outputformat, extensive_search, original_date, min_date, max_date
    )
    if abbr_result is not None:
        return abbr_result

    # expressions + text_content
    if extensive_search:
        date_expr = SLOW_PREPEND + DATE_EXPRESSIONS
    else:
        date_expr = FAST_PREPEND + DATE_EXPRESSIONS

    # first try in pruned tree
    search_tree, discarded = discard_unwanted(deepcopy(tree))
    dateresult = examine_date_elements(
        search_tree, date_expr, outputformat, extensive_search, min_date, max_date
    )
    if dateresult is not None:
        return dateresult

    # TODO: decide on this
    # search in discarded parts (e.g. archive.org-banner)
    # for subtree in discarded:
    #    dateresult = examine_date_elements(subtree, DATE_EXPRESSIONS,
    #        outputformat, extensive_search, min_date, max_date)
    #    if dateresult is not None:
    #        return dateresult

    # try time elements
    time_result = examine_time_elements(
        search_tree, outputformat, extensive_search, original_date, min_date, max_date
    )
    if time_result is not None:
        return time_result

    # clean before string search
    try:
        cleaned_html = HTML_CLEANER.clean_html(tree)
    # rare LXML error: no NULL bytes or control characters
    except ValueError:  # pragma: no cover
        cleaned_html = tree
        LOGGER.error("lxml cleaner error")

    # robust conversion to string
    try:
        htmlstring = tostring(cleaned_html, pretty_print=False, encoding="unicode")
    except UnicodeDecodeError:
        htmlstring = tostring(cleaned_html, pretty_print=False).decode(
            "utf-8", "ignore"
        )
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
    for title_elem in tree.iter("title", "h1"):
        attempt = try_date_expr(
            title_elem.text_content(),
            outputformat,
            extensive_search,
            min_date,
            max_date,
        )
        if attempt is not None:
            return attempt

    # last try: URL 2
    if url is not None:
        dateresult = extract_partial_url_date(url, outputformat, min_date, max_date)
        if dateresult is not None:
            return dateresult

    # try image elements
    img_result = img_search(tree, outputformat, min_date, max_date)
    if img_result is not None:
        return img_result

    # last resort
    if extensive_search:
        LOGGER.debug("extensive search started")
        # TODO: further tests & decide according to original_date
        reference = 0
        for segment in cleaned_html.xpath(FREE_TEXT_EXPRESSIONS):
            segment = segment.strip()
            # basic filter: minimum could be 8 or 9
            if not 6 < len(segment) < MAX_TEXT_SIZE:
                continue
            reference = compare_reference(
                reference,
                segment,
                outputformat,
                extensive_search,
                original_date,
                min_date,
                max_date,
            )
        # return
        converted = check_extracted_reference(
            reference, outputformat, min_date, max_date
        )
        if converted is not None:
            return converted
        # search page HTML
        return search_page(htmlstring, outputformat, original_date, min_date, max_date)

    return None

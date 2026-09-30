# pylint:disable-msg=E0611,I1101
"""Module bundling all functions needed to determine the date of HTML strings
or LXML trees.
"""

import logging
import re

from collections import Counter
from collections.abc import Sized
from copy import deepcopy
from datetime import datetime, timezone
from functools import partial

from lxml.etree import Element
from lxml.html import HtmlElement, tostring

# own
from .extractors import (
    discard_unwanted,
    extract_url_date,
    idiosyncrasies_search,
    img_search,
    json_search,
    regex_parse,
    pattern_search,
    try_date_expr_opts,
    FAST_TAGS,
    FREE_TEXT_EXPRESSIONS,
    DAY_RE,
    MONTH_RE,
    YEAR_RE,
    TIME_TZ_RE,
)
from .settings import (
    CLEANING_LIST,
    MAX_POSSIBLE_CANDIDATES,
    MAX_SEGMENT_LEN,
    MIN_SEGMENT_LEN,
)
from .utils import Extractor, clean_html, load_html, trim_text
from .validators import (
    correct_year,
    get_min_date,
    get_max_date,
    is_valid_format,
    pick,
    plausible_year_filter,
    validate,
    validate_ymd,
)

LOGGER = logging.getLogger(__name__)


def logstring(element: HtmlElement) -> str:
    """Format the element to be logged to a string."""
    return tostring(element, pretty_print=False, encoding="unicode").strip()


def serialize(tree: HtmlElement) -> str:
    "Robust conversion to string."
    try:
        return tostring(tree, pretty_print=False, encoding="unicode")
    except UnicodeDecodeError:
        return tostring(tree, pretty_print=False).decode("utf-8", "ignore")


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
    "og:regdate",
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

TIMESTAMP_PATTERN = re.compile(rf"({YEAR_RE}-{MONTH_RE}-{DAY_RE})({TIME_TZ_RE})")
# same without the mandatory time: fast-mode last resort only, see find_date
TIMESTAMP_LOOSE_PATTERN = re.compile(rf"({YEAR_RE}-{MONTH_RE}-{DAY_RE})({TIME_TZ_RE})?")

# component patterns
THREE_COMP_REGEX_A = re.compile(rf"({DAY_RE})[/.-]({MONTH_RE})[/.-]({YEAR_RE})")
THREE_COMP_REGEX_B = re.compile(
    rf"({DAY_RE})/({MONTH_RE})/([0-9]{{2}})|({DAY_RE})[.-]({MONTH_RE})[.-]([0-9]{{2}})"
)
TWO_COMP_REGEX = re.compile(rf"({MONTH_RE})[/.-]({YEAR_RE})")

# extensive search patterns
YEAR_PATTERN = re.compile(rf"^\D?({YEAR_RE})")
# bounded gap \D{0,99} (not \D*) avoids ReDoS
COPYRIGHT_PATTERN = re.compile(
    rf"(?:©|\&copy;|Copyright|\(c\))\D{{0,99}}(?:{YEAR_RE})?-?({YEAR_RE})\D"
)
THREE_PATTERN = re.compile(r"/([0-9]{4}/[0-9]{2}/[0-9]{2})[01/]")
THREE_LOOSE_PATTERN = re.compile(r"\D([0-9]{4}[/.-][0-9]{2}[/.-][0-9]{2})\D")
THREE_LOOSE_CATCH = re.compile(r"([0-9]{4})[/.-]([0-9]{2})[/.-]([0-9]{2})")
SELECT_YMD_PATTERN = re.compile(rf"\D({DAY_RE}[/.-]{MONTH_RE}[/.-][0-9]{{4}})\D")
SELECT_YMD_YEAR = re.compile(rf"({YEAR_RE})\D?$")
DATESTRINGS_PATTERN = re.compile(
    r"(\D19[0-9]{2}[01][0-9][0-3][0-9]\D|\D20[0-9]{2}[01][0-9][0-3][0-9]\D)"
)
DATESTRINGS_CATCH = re.compile(rf"({YEAR_RE})([01][0-9])([0-3][0-9])")
SLASHES_PATTERN = re.compile(
    rf"\D({DAY_RE}/{MONTH_RE}/[0129][0-9]|[0-3][0-9]\.[01][0-9]\.[0129][0-9])\D"
)
SLASHES_YEAR = re.compile(r"([0-9]{2})$")
YYYYMM_PATTERN = re.compile(r"\D([12][0-9]{3}[/.-](?:1[0-2]|0[1-9]))\D")
YYYYMM_CATCH = re.compile(rf"({YEAR_RE})[/.-](1[0-2]|0[1-9])")
MMYYYY_PATTERN = re.compile(rf"\D({MONTH_RE}[/.-][12][0-9]{{3}})\D")
SIMPLE_PATTERN = re.compile(rf"(?<!w3.org)\D({YEAR_RE})\D")

THREE_COMP_PATTERNS = (THREE_PATTERN, THREE_LOOSE_PATTERN)


def examine_text(
    text: str,
    options: Extractor,
) -> datetime | None:
    "Prepare text and try to extract a date."
    text = trim_text(text)
    if len(text) <= MIN_SEGMENT_LEN:
        return None
    text = NON_DIGITS_REGEX.sub("", text[:MAX_SEGMENT_LEN])
    return try_date_expr_opts(text, options)


def has_plausible_candidates(candidates: Sized) -> bool:
    "Check that the number of candidates is neither zero nor excessive."
    return 0 < len(candidates) <= MAX_POSSIBLE_CANDIDATES


ALWAYS_TAGS = frozenset({"footer", "small"})
ID_CLASS_CUES = re.compile("[Mm]eta|time|publish|footer")
CLASS_CUES = re.compile(
    "info|post_detail|block-content|byline|subline|posted|submitted|created-post|"
    "publication|author|autor|field-content|fa-clock-o|fa-calendar|fecha|parution"
)


def is_date_candidate(elem: HtmlElement) -> bool:
    "Mirrors the former XPath: of id and class, only the first in source order counts."
    first = itemprop = None
    for key, value in elem.attrib.items():
        if key == "itemprop":
            itemprop = value
        elif first is None and key in ("id", "class"):
            first = value
    for cue in (first, itemprop):
        if cue is not None:
            folded = cue.replace("D", "d")
            if "date" in folded or "datum" in folded:
                return True
    if first is None:
        return False
    if ID_CLASS_CUES.search(first):
        return True
    cls = elem.get("class")
    if cls is not None and CLASS_CUES.search(cls):
        return True
    idval = elem.get("id")
    return idval is not None and "footer-info-lastmod" in idval


def date_candidates(tree: HtmlElement, extensive_search: bool) -> list[HtmlElement]:
    "Collect date-bearing elements."
    elements = (
        tree.iterdescendants(Element)
        if extensive_search
        else tree.iterdescendants(*FAST_TAGS, *ALWAYS_TAGS)
    )
    return [e for e in elements if e.tag in ALWAYS_TAGS or is_date_candidate(e)]


def examine_elements(
    elements: list[HtmlElement], options: Extractor
) -> datetime | None:
    "Check candidate elements for date strings."
    if not has_plausible_candidates(elements):
        return None
    for elem in elements:
        # try element text and link title (Blogspot)
        for text in [elem.text_content(), elem.get("title", "")]:
            attempt = examine_text(text, options)
            if attempt:
                return attempt
    return None


def examine_header(
    tree: HtmlElement,
    options: Extractor,
) -> datetime | None:
    """
    Parse header elements to find date cues

    :param tree:
        LXML parsed tree object
    :type tree: LXML tree
    :param options:
        Options for extraction
    :type options: Extractor
    :return: Returns a valid date as a datetime, or None

    """
    headerdate, reserve = None, None
    tryfunc = partial(try_date_expr_opts, options=options)
    # loop through all meta elements
    for elem in tree.iterfind(".//meta"):
        # safeguard
        if "content" not in elem.attrib and "datetime" not in elem.attrib:
            continue
        content = elem.get("content")
        # name attribute, most frequent
        if "name" in elem.attrib:
            attribute = elem.get("name", "").lower()
            # url
            if attribute == "og:url":
                reserve = extract_url_date(content, options) or reserve
            # date
            elif attribute in DATE_ATTRIBUTES:
                LOGGER.debug("examining meta name: %s", logstring(elem))
                headerdate = tryfunc(content)
            # modified
            elif attribute in NAME_MODIFIED:
                LOGGER.debug("examining meta name: %s", logstring(elem))
                if not options.original:
                    headerdate = tryfunc(content)
                else:
                    reserve = tryfunc(content) or reserve
        # property attribute
        elif "property" in elem.attrib:
            attribute = elem.get("property", "").lower()
            if attribute in DATE_ATTRIBUTES or attribute in PROPERTY_MODIFIED:
                LOGGER.debug("examining meta property: %s", logstring(elem))
                attempt = tryfunc(content)
                if attempt is not None:
                    if attribute in (
                        DATE_ATTRIBUTES if options.original else PROPERTY_MODIFIED
                    ):
                        headerdate = attempt
                    # hurts precision
                    else:
                        reserve = attempt
        # itemprop
        elif "itemprop" in elem.attrib:
            attribute = elem.get("itemprop", "").lower()
            # original: store / updated: override date
            if attribute in ITEMPROP_ATTRS:
                LOGGER.debug("examining meta itemprop: %s", logstring(elem))
                attempt = tryfunc(elem.get("datetime") or content)
                # store value
                if attempt is not None:
                    if attribute in (
                        ITEMPROP_ATTRS_ORIGINAL
                        if options.original
                        else ITEMPROP_ATTRS_MODIFIED
                    ):
                        headerdate = attempt
                    # put on hold: hurts precision
                    # else:
                    #    reserve = attempt
            # reserve with copyrightyear
            elif attribute == "copyrightyear":
                LOGGER.debug("examining meta itemprop: %s", logstring(elem))
                if content is not None:
                    attempt = validate_ymd(content + "-01-01", options.min, options.max)
                    if attempt is not None:
                        reserve = attempt.replace(month=1, day=1)
        # pubdate, relatively rare
        elif "pubdate" in elem.attrib:
            if elem.get("pubdate", "").lower() == "pubdate":
                LOGGER.debug("examining meta pubdate: %s", logstring(elem))
                headerdate = tryfunc(content)
        # http-equiv, rare
        elif "http-equiv" in elem.attrib:
            attribute = elem.get("http-equiv", "").lower()
            if attribute in ("date", "last-modified"):
                LOGGER.debug("examining meta http-equiv: %s", logstring(elem))
                attempt = tryfunc(content)
                # "date" is original, "last-modified" is updated
                if (attribute == "date") == options.original:
                    headerdate = attempt
                else:
                    reserve = attempt or reserve
        # exit loop
        if headerdate is not None:
            break
    # if nothing was found, look for lower granularity (so far: "copyright year")
    if headerdate is None and reserve is not None:
        LOGGER.debug("opting for reserve date with less granularity")
        headerdate = reserve
    # return value
    return headerdate


def examine_abbr_elements(
    tree: HtmlElement,
    options: Extractor,
) -> datetime | None:
    """Scan the page for abbr elements and check if their content contains an eligible date"""
    elements = tree.findall(".//abbr")
    if has_plausible_candidates(elements):
        found: list[datetime | None] = []
        for elem in elements:
            # data-utime (mostly Facebook)
            if "data-utime" in elem.attrib:
                # untrusted: may be outside the platform timestamp range
                try:
                    candidate = datetime.fromtimestamp(
                        int(elem.get("data-utime", "")), tz=timezone.utc
                    )
                except (OSError, OverflowError, ValueError):
                    continue
                LOGGER.debug("data-utime found: %s", candidate)
                found.append(candidate)
            # class
            elif elem.get("class") in CLASS_ATTRS:
                # other attributes
                trytext = elem.get("title")
                if trytext is not None:
                    LOGGER.debug("abbr published-title found: %s", trytext)
                    # shortcut
                    if options.original:
                        attempt = try_date_expr_opts(trytext, options)
                        if attempt is not None:
                            return attempt
                    else:
                        found.append(try_date_expr_opts(trytext, options))
                        # faster execution
                        if any(found):
                            break
                # dates, not times of the day
                elif elem.text and len(elem.text) > 10:
                    LOGGER.debug("abbr published found: %s", elem.text)
                    found.append(try_date_expr_opts(elem.text, options))
        # return or try rescue in abbr content
        return pick(found, options) or examine_elements(elements, options)
    return None


def examine_time_elements(
    tree: HtmlElement,
    options: Extractor,
) -> datetime | None:
    """Scan the page for time elements and check if their content contains an eligible date"""
    elements = tree.findall(".//time")
    if has_plausible_candidates(elements):
        # scan all the tags and look for the newest one
        found: list[datetime | None] = []
        for elem in elements:
            datetime_attr = elem.get("datetime", "")
            # go for datetime
            if len(datetime_attr) > 6:
                class_attr = elem.get("class", "")
                # mode-specific shortcut attributes
                if options.original:
                    shortcut_flag = elem.get(
                        "pubdate"
                    ) == "pubdate" or class_attr.startswith(
                        ("entry-date", "entry-time")
                    )
                else:
                    shortcut_flag = class_attr == "updated"
                # analyze attribute
                if shortcut_flag:
                    LOGGER.debug("shortcut for time/datetime found: %s", datetime_attr)
                    attempt = try_date_expr_opts(datetime_attr, options)
                    if attempt is not None:
                        return attempt
                else:
                    LOGGER.debug("time/datetime found: %s", datetime_attr)
                    found.append(try_date_expr_opts(datetime_attr, options))
            # bare text in element
            elif elem.text is not None and len(elem.text) > 6:
                LOGGER.debug("time/datetime found in text: %s", elem.text)
                found.append(try_date_expr_opts(elem.text, options))
        return pick(found, options)
    return None


def select_candidate(occurrences: Counter[str], options: Extractor) -> str | None:
    "Select a YYYY-MM-DD key among the most frequent ones."
    if not has_plausible_candidates(occurrences):
        return None
    if len(occurrences) == 1:
        return next(iter(occurrences))
    firstselect = occurrences.most_common(10)
    LOGGER.debug("firstselect: %s", firstselect)
    (first, count1), (second, count2) = sorted(
        firstselect, reverse=not options.original
    )[:2]
    # the runner-up wins when from another year and more than half as frequent,
    # except on ties
    if count1 != count2 and first[:4] != second[:4] and count2 / count1 > 0.5:
        return second
    return first


def normalize(catch: re.Pattern[str], order: str, item: str) -> str:
    "Write the parts, named by order (y, m, d), as a YYYY-MM-DD key."
    match = catch.search(item)
    parts = dict(zip(order, (g for g in match.groups() if g)))  # type: ignore[union-attr]
    year = correct_year(int(parts["y"]))
    return f"{year}-{parts.get('m', '1').zfill(2)}-{parts.get('d', '1').zfill(2)}"


def search_pattern(
    htmlstring: str,
    pattern: re.Pattern[str],
    yearpat: re.Pattern[str],
    catch: re.Pattern[str],
    order: str,
    options: Extractor,
) -> datetime | None:
    "Count plausible matches as YMD keys, then select and validate one."
    candidates = plausible_year_filter(
        htmlstring,
        pattern=pattern,
        yearpat=yearpat,
        earliest=options.min,
        latest=options.max,
    )
    # count separator and order variants together
    normalized: Counter[str] = Counter()
    for item, count in candidates.items():
        normalized[normalize(catch, order, item)] += count
    best = select_candidate(normalized, options)
    return validate_ymd(best, options.min, options.max) if best else None


PAGE_PATTERNS = (
    # 3 components: target URL characteristics, then more loosely structured data
    (THREE_PATTERN, YEAR_PATTERN, THREE_LOOSE_CATCH, "ymd"),
    (THREE_LOOSE_PATTERN, YEAR_PATTERN, THREE_LOOSE_CATCH, "ymd"),
    (SELECT_YMD_PATTERN, SELECT_YMD_YEAR, THREE_COMP_REGEX_A, "dmy"),
    (DATESTRINGS_PATTERN, YEAR_PATTERN, DATESTRINGS_CATCH, "ymd"),
    (SLASHES_PATTERN, SLASHES_YEAR, THREE_COMP_REGEX_B, "dmy"),
    # 2 components
    (YYYYMM_PATTERN, YEAR_PATTERN, YYYYMM_CATCH, "ym"),
    (MMYYYY_PATTERN, SELECT_YMD_YEAR, TWO_COMP_REGEX, "my"),
)


def search_page(htmlstring: str, options: Extractor) -> datetime | None:
    """
    Opportunistically search the HTML text for common text patterns

    :param htmlstring:
        The HTML document in string format, potentially cleaned and stripped to
        the core (much faster)
    :type htmlstring: string
    :param options:
        Define extraction options
    :type options: Extractor
    :return: Returns a valid date as a datetime, or None

    """
    # copyright symbol
    copydate = search_pattern(
        htmlstring, COPYRIGHT_PATTERN, YEAR_PATTERN, YEAR_PATTERN, "y", options
    )
    copyear = copydate.year if copydate else 0
    LOGGER.debug("copyright year/footer: %s", copyear)

    # candidates must not predate the copyright year
    for step in PAGE_PATTERNS:
        result = search_pattern(htmlstring, *step, options)
        if result is not None and result.year >= copyear:
            return result

    # full-blown text regex on all HTML
    result = validate(regex_parse(htmlstring), options.min, options.max)
    if result is not None and result.year >= copyear:
        return result

    # catchall: copyright mention
    if copydate is not None:
        return copydate

    # last resort: 1 component
    return search_pattern(
        htmlstring, SIMPLE_PATTERN, YEAR_PATTERN, YEAR_PATTERN, "y", options
    )


def find_date(
    htmlobject: bytes | str | HtmlElement,
    extensive_search: bool = True,
    original_date: bool = False,
    outputformat: str = "%Y-%m-%d",
    url: str | None = None,
    verbose: bool = False,
    min_date: datetime | str | None = None,
    max_date: datetime | str | None = None,
    deferred_url_extractor: bool = False,
) -> str | None:
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
    if not is_valid_format(outputformat):
        return None

    # define options and time boundaries
    options = Extractor(
        extensive_search, get_max_date(max_date), get_min_date(min_date), original_date
    )
    result = date_from_tree(
        tree, options, url, deferred_url_extractor, isinstance(htmlobject, HtmlElement)
    )
    return result.strftime(outputformat) if result is not None else None


def date_from_tree(
    tree: HtmlElement,
    options: Extractor,
    url: str | None,
    deferred_url_extractor: bool,
    caller_tree: bool,
) -> datetime | None:
    "Run the extraction cascade on a parsed tree, copied first if caller_tree."
    extensive_search = options.extensive

    # URL
    if url is None:
        # probe for canonical links
        urlelem = tree.find('.//link[@rel="canonical"]')
        if urlelem is not None:
            url = urlelem.get("href")

    # direct processing of URL info
    url_result = extract_url_date(url, options)
    if url_result is not None and not deferred_url_extractor:
        return url_result

    # first try header
    # then try to use JSON data
    result = examine_header(tree, options) or json_search(tree, options)
    if result is not None:
        return result

    # deferred processing of URL info (may be moved even further down if necessary)
    if deferred_url_extractor and url_result is not None:
        return url_result

    # try abbr elements
    abbr_result = examine_abbr_elements(
        tree,
        options,
    )
    if abbr_result is not None:
        return abbr_result

    # first, prune tree
    # only copy the tree if the caller passed one in: when we parsed it ourselves
    # (string/bytes/URL input) we own it and can clean it in place, avoiding a
    # costly deepcopy of the whole document
    pruning_tree = deepcopy(tree) if caller_tree else tree
    try:
        search_tree = discard_unwanted(clean_html(pruning_tree, CLEANING_LIST))
    # rare LXML error: no NULL bytes or control characters
    except ValueError:  # pragma: no cover
        # pruning_tree, not tree: it is ours in both cases, and the fast-mode
        # fallback below strips this tree in place
        search_tree = pruning_tree
        LOGGER.error("lxml cleaner error")

    result = (
        examine_elements(date_candidates(search_tree, extensive_search), options)
        or examine_elements(search_tree.xpath(".//title|.//h1"), options)
        or examine_time_elements(search_tree, options)
    )
    if result is not None:
        return result

    htmlstring = serialize(search_tree)

    # date regex timestamp rescue
    # try image elements
    # precise patterns and idiosyncrasies
    result = (
        pattern_search(htmlstring, TIMESTAMP_PATTERN, options)
        or img_search(search_tree, options)
        or idiosyncrasies_search(htmlstring, options)
    )
    if result is not None:
        return result

    # fast mode has no search_page fallback: accept a bare date, but from text
    # only — itertext() skips comments and attributes yet keeps tail text
    if not extensive_search:
        clean_html(search_tree, ["script", "style"])
        text = " ".join(search_tree.itertext())
        return pattern_search(text, TIMESTAMP_LOOSE_PATTERN, options)

    LOGGER.debug("extensive search started")
    # TODO: further tests & decide according to original_date
    segments = (s.strip() for s in FREE_TEXT_EXPRESSIONS(search_tree))
    converted = pick(
        (
            try_date_expr_opts(s, options)
            for s in segments
            if MIN_SEGMENT_LEN < len(s) < MAX_SEGMENT_LEN
        ),
        options,
    )
    # return or search page HTML
    return converted or search_page(htmlstring, options)

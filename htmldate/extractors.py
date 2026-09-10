# pylint:disable-msg=E0611,I1101
"""
Custom parsers and XPath expressions for date extraction
"""

import logging
import re

from collections.abc import Iterator
from datetime import datetime
from functools import lru_cache
from itertools import islice
from typing import TYPE_CHECKING

from dateutil.parser import parse as dateutil_parse

from lxml.etree import XPath
from lxml.html import HtmlElement

# own
from .settings import CACHE_SIZE, MAX_SEGMENT_LEN
from .utils import Extractor, remove_if_attached, trim_text
from .validators import convert_date, correct_year, is_valid_date, validate_and_convert

if TYPE_CHECKING:  # pragma: no cover
    from dateparser import DateDataParser  # type: ignore[attr-defined]

LOGGER = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def get_external_parser() -> "DateDataParser":
    "Lazy import, unused in fast mode."
    from dateparser import DateDataParser  # type: ignore[attr-defined]

    return DateDataParser(
        languages=None,
        locales=None,
        region=None,
        settings={
            "NORMALIZE": True,  # False may be faster
            "PARSERS": [
                "custom-formats",
                "absolute-time",
            ],
            "PREFER_DATES_FROM": "past",
            "PREFER_LOCALE_DATE_ORDER": True,
            "RETURN_AS_TIMEZONE_AWARE": False,
            "STRICT_PARSING": True,
        },
    )


FAST_TAGS = ("div", "h2", "h3", "h4", "li", "p", "span", "time", "ul")
# further tests needed: b, em, font, i, strong
FAST_PREPEND = ".//*[" + " or ".join(f"self::{t}" for t in FAST_TAGS) + "]"
FREE_TEXT_EXPRESSIONS = XPath(FAST_PREPEND + "/text()")

# discard parts of the webpage
# archive.org banner inserts
DISCARD_EXPRESSIONS = XPath('.//div[@id="wm-ipp-base" or @id="wm-ipp"]')
# not discarded for consistency (see above):
# .//footer
# .//*[(self::div or self::section)][@id="footer" or @class="footer"]

DAY_RE = "[0-3]?[0-9]"
MONTH_RE = "[0-1]?[0-9]"
# keep the (?:...): interpolated bare, the "|" would split the enclosing group
YEAR_RE = "(?:199[0-9]|20[0-3][0-9])"

# regex cache
YMD_NO_SEP_PATTERN = re.compile(r"\b(\d{8})\b")
YMD_PATTERN = re.compile(
    rf"(?:\D|^)(?:(?P<year>{YEAR_RE})[\-/.](?P<month>{MONTH_RE})[\-/.](?P<day>{DAY_RE})|"
    rf"(?P<day2>{DAY_RE})[\-/.](?P<month2>{MONTH_RE})[\-/.](?P<year2>\d{{2,4}}))(?:\D|$)"
)
YM_PATTERN = re.compile(
    rf"(?:\D|^)(?:(?P<year>{YEAR_RE})[\-/.](?P<month>{MONTH_RE})|"
    rf"(?P<month2>{MONTH_RE})[\-/.](?P<year2>{YEAR_RE}))(?:\D|$)"
)

REGEX_MONTHS = """
January?|February?|March|A[pv]ril|Ma[iy]|Jun[ei]|Jul[iy]|August|September|O[ck]tober|November|De[csz]ember|
Jan|Feb|M[aä]r|Apr|Jun|Jul|Aug|Sep|O[ck]t|Nov|De[cz]|
Januari|Februari|Maret|Mei|Agustus|
Jänner|Feber|März|
janvier|février|mars|juin|juillet|aout|septembre|octobre|novembre|décembre|
Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık|
Oca|Şub|Mar|Nis|Haz|Tem|Ağu|Eyl|Eki|Kas|Ara
"""  # todo: check "août"
LONG_TEXT_PATTERN = re.compile(
    rf"""(?P<month>{REGEX_MONTHS})\s
(?P<day>{DAY_RE})(?:st|nd|rd|th)?,? (?P<year>{YEAR_RE})|
(?P<day2>{DAY_RE})(?:st|nd|rd|th|\.)? (?:of )?
(?P<month2>{REGEX_MONTHS})[,.]? (?P<year2>{YEAR_RE})""".replace("\n", ""),
    re.I,
)

YEAR_CANDIDATES = re.compile(YEAR_RE)

COMPLETE_URL = re.compile(rf"\D({YEAR_RE})[/_-]({MONTH_RE})[/_-]({DAY_RE})(?:\D|$)")

# optional ISO-8601 time-of-day and time zone suffix (e.g. "T08:37:00+05:30")
TIME_TZ_RE = r"[T ][0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:?[0-9]{2})?"

JSON_MODIFIED = re.compile(
    rf'"dateModified": ?"({YEAR_RE}-{MONTH_RE}-{DAY_RE})({TIME_TZ_RE})?', re.I
)
JSON_PUBLISHED = re.compile(
    rf'"datePublished": ?"({YEAR_RE}-{MONTH_RE}-{DAY_RE})({TIME_TZ_RE})?', re.I
)

# English, French, German, Indonesian and Turkish month names
MONTHS = [
    ("jan", "januar", "jänner", "january", "januari", "janvier", "ocak", "oca"),
    ("feb", "februar", "feber", "february", "februari", "février", "şubat", "şub"),
    ("mar", "mär", "märz", "march", "maret", "mart", "mars"),
    ("apr", "april", "avril", "nisan", "nis"),
    ("may", "mai", "mei", "mayıs"),
    ("jun", "juni", "june", "juin", "haziran", "haz"),
    ("jul", "juli", "july", "juillet", "temmuz", "tem"),
    ("aug", "august", "agustus", "ağustos", "ağu", "aout"),
    ("sep", "september", "septembre", "eylül", "eyl"),
    ("oct", "oktober", "october", "octobre", "okt", "ekim", "eki"),
    ("nov", "november", "kasım", "kas", "novembre"),
    ("dec", "dez", "dezember", "december", "desember", "décembre", "aralık", "ara"),
]

# regex, not a dict: str.lower() disagrees with re.I on dotted/dotless i (e.g. "MAYIS")
MONTH_PATTERNS = [
    re.compile(rf"^(?:{'|'.join(map(re.escape, m))})$", re.I) for m in MONTHS
]


def _month_number(token: str) -> int | None:
    "Month number for a name in any supported language."
    return next((i for i, p in enumerate(MONTH_PATTERNS, 1) if p.match(token)), None)


# gate for try_date_expr
TEXT_DATE_PATTERN = re.compile(r"[.:,_/ -]")
YEAR_OR_MONTH = re.compile(
    rf"(?<!\d)\d{{4}}(?!\d)|\b(?:{REGEX_MONTHS})\b".replace("\n", ""), re.I
)
DAY_TOKEN = re.compile(r"(?<!\d)\d{1,2}(?!\d)")

DISCARD_PATTERNS = re.compile(
    r"^\d{2}:\d{2}(?: |:|$)|"
    r"^\D*\d{4}\D*$|"
    r"[$€¥Ұ£¢₽₱฿#₹]|"  # currency symbols and special characters
    r"[A-Z]{3}[^A-Z]|"  # currency codes
    r"(?:^|\D)(?:\+\d{2}|\d{3}|\d{5})\D|"  # tel./IPs/postal codes
    r"ftps?|https?|sftp|"  # protocols
    r"\.(?:com|net|org|info|gov|edu|de|fr|io)\b|"  # TLDs
    r"IBAN|[A-Z]{2}[0-9]{2}|"  # bank accounts
    r"®"  # ©
)

# use of regex module for speed?
# numeric core shared by all TEXT_PATTERNS alternatives, used as prefilter
DATE_CORE_PATTERN = re.compile(r"[0-9]{1,4}[./][0-9]{1,2}[./][0-9]{2,4}")

# gap-runs bounded to {0,9} (ReDoS + keeps matches within the prefilter windows)
TEXT_PATTERNS = re.compile(
    r'(?:date[^0-9"]{,20}|updated|last-modified|published|posted|on)[ :]{0,9}?([0-9]{1,4})[./]([0-9]{1,2})[./]([0-9]{2,4})|'  # EN
    r"(?:Datum|Stand|Veröffentlicht am):? ?([0-9]{1,2})\.([0-9]{1,2})\.([0-9]{2,4})|"  # DE
    r"(?:güncellen?me|yayı(?:m|n)lan?ma) {0,9}?(?:tarihi)? {0,9}?:? {0,9}?([0-9]{1,2})[./]([0-9]{1,2})[./]([0-9]{2,4})|"
    r"([0-9]{1,2})[./]([0-9]{1,2})[./]([0-9]{2,4}) {0,9}?(?:'de|'da|'te|'ta|’de|’da|’te|’ta|tarihinde) {0,9}(?:güncellendi|yayı(?:m|n)landı)",  # TR
    re.I,
)


def discard_unwanted(tree: HtmlElement) -> HtmlElement:
    """Delete unwanted sections of an HTML document."""
    for subtree in DISCARD_EXPRESSIONS(tree):
        remove_if_attached(subtree)
    return tree


def extract_url_date(
    testurl: str | None,
    options: Extractor,
) -> str | None:
    """Extract the date out of an URL string complying with the Y-M-D format"""
    if testurl is not None:
        match = COMPLETE_URL.search(testurl)
        if match:
            LOGGER.debug("found date in URL: %s", match[0])
            try:
                dateobject = datetime(int(match[1]), int(match[2]), int(match[3]))
                return validate_and_convert(
                    dateobject, options.format, earliest=options.min, latest=options.max
                )
            except ValueError as err:  # pragma: no cover
                LOGGER.debug("conversion error: %s %s", match[0], err)
    return None


def try_swap_values(day: int, month: int) -> tuple[int, int]:
    """Swap day and month values if it seems feasible."""
    return (month, day) if month > 12 and day <= 12 else (day, month)


def _build_dmy(day: int, month: int, year: int) -> datetime:
    "Build a datetime from day/month/year, fixing 2-digit years and day/month order."
    year = correct_year(year)
    day, month = try_swap_values(day, month)
    return datetime(year, month, day)


def regex_parse(string: str) -> datetime | None:
    """Try full-text parse for date elements using a series of regular expressions
    with particular emphasis on English, French, German and Turkish"""
    # https://github.com/vi3k6i5/flashtext ?
    # multilingual day-month-year + American English patterns
    # search windows end at each year token
    match = None
    prev = 0
    for year in YEAR_CANDIDATES.finditer(string):
        match = LONG_TEXT_PATTERN.search(
            string, max(prev, year.start() - 60), year.end()
        )
        if match:
            break
        prev = year.start()
    if not match:
        return None
    groups = (
        ("day", "month", "year")
        if match.lastgroup == "year"
        else ("day2", "month2", "year2")
    )
    month = _month_number(match.group(groups[1]))
    if month is None:  # pragma: no cover — every REGEX_MONTHS name is in MONTHS
        return None
    # process and return
    try:
        dateobject = _build_dmy(
            int(match.group(groups[0])),
            month,
            int(match.group(groups[2])),
        )
    except ValueError:
        return None
    LOGGER.debug("multilingual text found: %s", dateobject)
    return dateobject


def _parse_yyyymmdd(digits: str) -> datetime:
    "Build a datetime from a leading 8-digit YYYYMMDD run."
    return datetime(int(digits[:4]), int(digits[4:6]), int(digits[6:8]))


def _date_candidates(string: str) -> Iterator[datetime | None]:
    "Yield datetime candidates for custom_parse, in decreasing priority order."
    # 1. shortcut
    if string[:4].isdigit():
        candidate = None
        # a. '201709011234' not covered by dateparser, and regex too slow
        if string[4:8].isdigit():
            try:
                candidate = _parse_yyyymmdd(string)
            except ValueError:
                LOGGER.debug("8-digit error: %s", string[:8])
        # b. much faster than extensive parsing
        else:
            try:
                candidate = datetime.fromisoformat(string)
            except ValueError:
                LOGGER.debug("not an ISO date string: %s", string)
                try:
                    candidate = dateutil_parse(string, fuzzy=False)  # ignoretz=True
                except (OverflowError, TypeError, ValueError):
                    LOGGER.debug("dateutil parsing error: %s", string)
        yield candidate

    # 2. Try YYYYMMDD, use regex
    match = YMD_NO_SEP_PATTERN.search(string)
    if match:
        try:
            yield _parse_yyyymmdd(match[1])
        except ValueError:
            LOGGER.debug("YYYYMMDD value error: %s", match[0])

    # 3. Try the very common YMD, Y-M-D, and D-M-Y patterns
    match = YMD_PATTERN.search(string)
    if match:
        try:
            if match.lastgroup == "day":
                yield datetime(
                    int(match.group("year")),
                    int(match.group("month")),
                    int(match.group("day")),
                )
            else:
                yield _build_dmy(
                    int(match.group("day2")),
                    int(match.group("month2")),
                    int(match.group("year2")),
                )
        except ValueError:  # pragma: no cover
            LOGGER.debug("regex value error: %s", match[0])

    # 4. Try the Y-M and M-Y patterns (one alternative matches; other groups are None)
    match = YM_PATTERN.search(string)
    if match:
        try:
            year = match.group("year") or match.group("year2")
            month = match.group("month") or match.group("month2")
            yield datetime(int(year), int(month), 1)
        except ValueError:
            LOGGER.debug("Y-M value error: %s", match[0])

    # 5. Try the other regex pattern
    yield regex_parse(string)


def custom_parse(
    string: str, outputformat: str, min_date: datetime, max_date: datetime
) -> str | None:
    """Try to bypass the slow dateparser"""
    LOGGER.debug("custom parse test: %s", string)
    for candidate in _date_candidates(string):
        result = validate_and_convert(
            candidate, outputformat, earliest=min_date, latest=max_date
        )
        if result is not None:
            return result
    return None


def external_date_parser(string: str, outputformat: str) -> str | None:
    """Use dateutil parser or dateparser module according to system settings"""
    LOGGER.debug("send to external parser: %s", string)
    try:
        target = get_external_parser().get_date_data(string)["date_obj"]
    # 2 types of errors possible
    except (OverflowError, ValueError) as err:  # pragma: no cover
        target = None
        LOGGER.error("external parser error: %s %s", string, err)
    # issue with data type
    return target.strftime(outputformat) if target else None


@lru_cache(maxsize=CACHE_SIZE)
def try_date_expr(
    string: str | None,
    outputformat: str,
    extensive_search: bool,
    min_date: datetime,
    max_date: datetime,
) -> str | None:
    """Use a series of heuristics and rules to parse a potential date expression"""
    if not string:
        return None

    # trim
    string = trim_text(string)[:MAX_SEGMENT_LEN]

    # formal constraint: 4 to 18 digits
    if not string or not 4 <= sum(map(str.isdigit, string)) <= 18:
        return None

    # check if string only contains time/single year or digits and not a date
    if DISCARD_PATTERNS.search(string):
        return None

    # try to parse using the faster method
    customresult = custom_parse(string, outputformat, min_date, max_date)
    if customresult is not None:
        return customresult

    # use slow but extensive search
    # only plausible dates reach the slow external parser
    if (
        extensive_search
        and TEXT_DATE_PATTERN.search(string)
        and (match := YEAR_OR_MONTH.search(string)) is not None
        and (not match[0].isdigit() or min_date.year <= int(match[0]) <= max_date.year)
        and DAY_TOKEN.search(string)
    ):
        # send to date parser
        dateparser_result = external_date_parser(string, outputformat)
        if is_valid_date(
            dateparser_result, outputformat, earliest=min_date, latest=max_date
        ):
            return dateparser_result

    return None


def try_date_expr_opts(string: str | None, options: Extractor) -> str | None:
    "Uncached wrapper for try_date_expr: Extractor is identity-hashed, so caching it is useless."
    return try_date_expr(
        string, options.format, options.extensive, options.min, options.max
    )


def img_search(
    tree: HtmlElement,
    options: Extractor,
) -> str | None:
    """Skim through image elements"""
    element = tree.find('.//meta[@property="og:image"][@content]')
    if element is not None:
        return extract_url_date(
            element.get("content"),
            options,
        )
    return None


# strftime directives carrying time of day or time zone
TIME_TZ_DIRECTIVES = ("%H", "%I", "%M", "%S", "%f", "%z", "%Z", "%p", "%X", "%c")


def pattern_search(
    text: str,
    date_pattern: re.Pattern[str],
    options: Extractor,
) -> str | None:
    "Look for date expressions using a regular expression on a string of text."
    match = date_pattern.search(text)
    if not match or not is_valid_date(
        match[1], "%Y-%m-%d", earliest=options.min, latest=options.max
    ):
        return None
    LOGGER.debug("regex found: %s %s", date_pattern, match[0])
    # carry time of day and time zone through when the output format needs them
    # (group 1 is the date, the optional group 2 the time/tz suffix)
    full = (
        custom_parse(match[1] + match[2], options.format, options.min, options.max)
        if match.lastindex
        and match.lastindex >= 2
        and match[2]
        and any(directive in options.format for directive in TIME_TZ_DIRECTIVES)
        else None
    )
    return full or convert_date(match[1], "%Y-%m-%d", options.format)


def json_search(
    tree: HtmlElement,
    options: Extractor,
) -> str | None:
    """Look for JSON time patterns in JSON sections of the tree"""
    # determine pattern
    json_pattern = JSON_PUBLISHED if options.original else JSON_MODIFIED
    # look throughout the HTML tree
    for elem in tree.xpath(
        './/script[@type="application/ld+json" or @type="application/settings+json"]'
    ):
        if not elem.text or '"date' not in elem.text:
            continue
        result = pattern_search(elem.text, json_pattern, options)
        if result is not None:
            return result
    return None


def idiosyncrasies_search(
    htmlstring: str,
    options: Extractor,
) -> str | None:
    """Look for author-written dates throughout the web page"""
    # probe ±60-char windows around numeric cores (enough: gap-runs are bounded),
    # then re-search unbounded so the result equals a full slow scan
    match = None
    cores = DATE_CORE_PATTERN.finditer(htmlstring)
    for core in islice(cores, 1000):
        start = max(0, core.start() - 60)
        if TEXT_PATTERNS.search(htmlstring, start, core.end() + 60):  # EN+DE+TR
            match = TEXT_PATTERNS.search(htmlstring, start)
            break
    else:
        if next(cores, None) is not None:  # cap hit on a date-dense document
            match = TEXT_PATTERNS.search(htmlstring)
    if match:
        parts = list(filter(None, match.groups()))

        try:
            if len(parts[0]) == 4:  # year in first position
                candidate = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
            else:  # len(parts[2]) in (2, 4):  # DD/MM/YY
                candidate = _build_dmy(int(parts[0]), int(parts[1]), int(parts[2]))
            return validate_and_convert(
                candidate, options.format, earliest=options.min, latest=options.max
            )
        except (IndexError, ValueError):
            LOGGER.debug("cannot process idiosyncrasies: %s", match[0])

    return None

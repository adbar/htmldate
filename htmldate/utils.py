# pylint:disable-msg=E0611,I1101
"""
Module bundling functions related to HTML processing.
"""

import logging
import re

from dataclasses import dataclass
from datetime import datetime

import urllib3

# CChardet is faster and can be more accurate
try:
    from cchardet import detect as cchardet_detect
except ImportError:
    cchardet_detect = None
from charset_normalizer import from_bytes

from lxml.html import HtmlElement, HTMLParser, fromstring

from .settings import MAX_FILE_SIZE

LOGGER = logging.getLogger(__name__)

UNICODE_ALIASES: set[str] = {"utf-8", "utf_8"}

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
RETRY_STRATEGY = urllib3.util.Retry(
    total=3,
    connect=0,
    status_forcelist=[429, 500, 502, 503, 504],
)
HTTP_POOL = urllib3.PoolManager(retries=RETRY_STRATEGY)

HTML_PARSER = HTMLParser(
    collect_ids=False, default_doctype=False, encoding="utf-8", remove_pis=True
)

DOCTYPE_TAG = re.compile("^< ?! ?DOCTYPE.+?/ ?>", re.I)
FAULTY_HTML = re.compile(r"(<html.*?)\s*/>", re.I)


# eq=False keeps identity-based hashing so instances stay usable as lru_cache keys
@dataclass(slots=True, eq=False)
class Extractor:
    "Defines a class to store all extraction options."

    extensive: bool
    max: datetime
    min: datetime
    original: bool
    format: str


def is_wrong_document(data: str | bytes | HtmlElement | None) -> bool:
    "Check if the input object is suitable to be processed."
    return not data or len(data) > MAX_FILE_SIZE


def isutf8(data: bytes) -> bool:
    """Simple heuristic to determine if a bytestring uses standard unicode encoding"""
    try:
        data.decode("UTF-8")
    except UnicodeDecodeError:
        return False
    return True


def detect_encoding(bytesobject: bytes) -> list[str]:
    """Read all input or first chunk and return a list of encodings"""
    # alternatives: https://github.com/scrapy/w3lib/blob/master/w3lib/encoding.py
    # unicode-test
    if isutf8(bytesobject):
        return ["utf-8"]

    guesses = []
    # additional module
    if cchardet_detect is not None:
        cchardet_guess = cchardet_detect(bytesobject)["encoding"]
        if cchardet_guess is not None:
            guesses.append(cchardet_guess.lower())

    # try charset_normalizer on first part, fallback on full document
    detection_results = from_bytes(bytesobject[:15000]) or from_bytes(bytesobject)
    guesses.extend([r.encoding for r in detection_results])

    # return alternatives, it cannot be utf-8 (tested above)
    return [g for g in guesses if g not in UNICODE_ALIASES]


def decode_file(filecontent: bytes | str) -> str:
    """Guess bytestring encoding and try to decode to Unicode string.
    Resort to destructive conversion otherwise."""
    # init
    if isinstance(filecontent, str):
        return filecontent
    htmltext = None
    # encoding
    for guessed_encoding in detect_encoding(filecontent):
        try:
            htmltext = filecontent.decode(guessed_encoding)
        except (LookupError, UnicodeDecodeError):  # VISCII: lookup
            LOGGER.warning("wrong encoding detected: %s", guessed_encoding)
        else:
            break
    # return original content if nothing else succeeded
    return htmltext or str(filecontent, encoding="utf-8", errors="replace")


def decode_response(response: urllib3.response.HTTPResponse | bytes) -> str:
    """Read the urllib3 object corresponding to the server response, then
    try to guess its encoding and decode it to return a unicode string"""
    # urllib3 response object / bytes switch
    if isinstance(response, urllib3.response.HTTPResponse):
        resp_content = response.data
    else:
        resp_content = response
    return decode_file(resp_content)


def fetch_url(url: str) -> str | None:
    """Fetches page using urllib3 and decodes the response.

    Args:
        url: URL of the page to fetch.

    Returns:
        HTML code as string, or Urllib3 response object (headers + body), or empty string in case
        the result is invalid, or None if there was a problem with the network.

    """
    # send
    try:
        # read by streaming chunks (stream=True, iter_content=xx)
        # so we can stop downloading as soon as MAX_FILE_SIZE is reached
        response = HTTP_POOL.request("GET", url, timeout=30)
    except Exception as err:
        LOGGER.error("download error: %s %s", url, err)  # sys.exc_info()[0]
    else:
        # safety checks
        if response.status != 200:
            LOGGER.error("not a 200 response: %s for URL %s", response.status, url)
        elif is_wrong_document(response.data):
            LOGGER.error("incorrect input data for URL %s", url)
        else:
            return decode_response(response.data)
    return None


def is_dubious_html(beginning: str) -> bool:
    "Assess if the object is proper HTML (awith a corresponding tag or declaration)."
    return "html" not in beginning


def repair_faulty_html(htmlstring: str, beginning: str) -> str:
    "Repair faulty HTML strings to make then palatable for libxml2."
    # libxml2/LXML issue: https://bugs.launchpad.net/lxml/+bug/1955915
    if "doctype" in beginning:
        firstline, _, rest = htmlstring.partition("\n")
        htmlstring = DOCTYPE_TAG.sub("", firstline, count=1) + "\n" + rest
    # other issue with malformed documents: check first three lines
    for i, line in enumerate(htmlstring.splitlines()):
        if "<html" in line and line.endswith("/>"):
            htmlstring = FAULTY_HTML.sub(r"\1>", htmlstring, count=1)
            break
        if i > 2:
            break
    return htmlstring


def fromstring_bytes(htmlobject: str) -> HtmlElement | None:
    "Try to pass bytes to LXML parser."
    try:
        return fromstring(htmlobject.encode("utf8"), parser=HTML_PARSER)
    except Exception as err:
        LOGGER.error("lxml parser bytestring %s", err)
    return None


def load_html(htmlobject: bytes | str | HtmlElement) -> HtmlElement | None:
    """Load object given as input and validate its type
    (accepted: lxml.html tree, bytestring and string)
    """
    # use tree directly
    if isinstance(htmlobject, HtmlElement):
        return htmlobject
    # do not accept any other type after this point
    if not isinstance(htmlobject, (bytes, str)):
        raise TypeError(f"incompatible input type: {type(htmlobject)}")
    # the string is a URL, download it
    if (
        isinstance(htmlobject, str)
        and htmlobject.startswith("http")
        and " " not in htmlobject
    ):
        LOGGER.debug("URL detected, downloading: %s", htmlobject)
        downloaded = fetch_url(htmlobject)
        # log the error and quit
        if downloaded is None:
            raise ValueError(f"URL couldn't be processed: {htmlobject}")
        htmlobject = downloaded
    # start processing
    tree = None
    # try to guess encoding and decode file: if None then keep original
    htmlobject = decode_file(htmlobject)
    # sanity checks
    beginning = htmlobject[:50].lower()
    # repair first
    htmlobject = repair_faulty_html(htmlobject, beginning)
    # first pass: use Unicode string
    fallback_parse = False
    try:
        tree = fromstring(htmlobject, parser=HTML_PARSER)
    except ValueError:
        # "Unicode strings with encoding declaration are not supported."
        fallback_parse = True
        tree = fromstring_bytes(htmlobject)
    except Exception as err:  # pragma: no cover
        LOGGER.error("lxml parsing failed: %s", err)
    # second pass: try passing bytes to LXML
    if (tree is None or len(tree) < 1) and not fallback_parse:
        tree = fromstring_bytes(htmlobject)
    # rejection test: is it (well-formed) HTML at all?
    # log parsing errors
    if tree is not None and is_dubious_html(beginning) and len(tree) < 2:
        LOGGER.error(
            "parsed tree length: %s, wrong data type or not valid HTML", len(tree)
        )
        tree = None
    return tree


def clean_html(tree: HtmlElement, elemlist: list[str]) -> HtmlElement:
    "Delete selected elements."
    for element in tree.iter(elemlist):
        # drop_tree() keeps the element's tail text (a date may sit right after a
        # cleaned media element); fall back to remove() if it is unavailable
        try:
            element.drop_tree()
        except AttributeError:  # pragma: no cover
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)
    return tree


def trim_text(string: str) -> str:
    "Remove superfluous space and normalize remaining space."
    return " ".join(string.split())

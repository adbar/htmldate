# pylint:disable-msg=E0611,I1101
"""
Module bundling functions related to HTML processing.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license


# standard
import logging
import re

from typing import Any, List, Optional, Set, Union

import urllib3


# CChardet is faster and can be more accurate
try:
    from cchardet import detect as cchardet_detect  # type: ignore
except ImportError:
    cchardet_detect = None
from charset_normalizer import from_bytes

from lxml.html import HtmlElement, HTMLParser, fromstring  # type: ignore

from .settings import MAX_FILE_SIZE, MIN_FILE_SIZE


LOGGER = logging.getLogger(__name__)

UNICODE_ALIASES: Set[str] = {"utf-8", "utf_8"}

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


def isutf8(data: bytes) -> bool:
    """Simple heuristic to determine if a bytestring uses standard unicode encoding"""
    try:
        data.decode("UTF-8")
    except UnicodeDecodeError:
        return False
    else:
        return True


def detect_encoding(bytesobject: bytes) -> List[str]:
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
    # return alternatives
    if len(detection_results) > 0:
        guesses.extend([r.encoding for r in detection_results])
    # it cannot be utf-8 (tested above)
    return [g for g in guesses if g not in UNICODE_ALIASES]


def decode_file(filecontent: Union[bytes, str]) -> str:
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
            htmltext = None
        else:
            break
    # return original content if nothing else succeeded
    return htmltext or str(filecontent, encoding="utf-8", errors="replace")


def decode_response(response: Any) -> str:
    """Read the urllib3 object corresponding to the server response, then
    try to guess its encoding and decode it to return a unicode string"""
    # urllib3 response object / bytes switch
    if isinstance(response, urllib3.response.HTTPResponse) or hasattr(response, "data"):
        resp_content = response.data
    else:
        resp_content = response
    return decode_file(resp_content)


def fetch_url(url: str) -> Optional[str]:
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
        response = HTTP_POOL.request("GET", url, timeout=30)  # type: ignore
    except Exception as err:
        LOGGER.error("download error: %s %s", url, err)  # sys.exc_info()[0]
    else:
        # safety checks
        if response.status != 200:
            LOGGER.error("not a 200 response: %s for URL %s", response.status, url)
        elif (
            response.data is None
            or len(response.data) < MIN_FILE_SIZE
            or len(response.data) > MAX_FILE_SIZE
        ):
            LOGGER.error("incorrect input data for URL %s", url)
        else:
            return decode_response(response.data)
    return None


def is_dubious_html(htmlobject: Union[bytes, str]) -> bool:
    "Assess if the object is proper HTML (with a corresponding declaration)."
    if isinstance(htmlobject, bytes):
        if (
            "html"
            not in htmlobject[:50].decode(encoding="ascii", errors="ignore").lower()
        ):
            return True
    elif isinstance(htmlobject, str):
        if "html" not in htmlobject[:50].lower():
            return True
    return False


def load_html(htmlobject: HtmlElement) -> HtmlElement:
    """Load object given as input and validate its type
    (accepted: lxml.html tree, bytestring and string)
    """
    # use tree directly
    if isinstance(htmlobject, HtmlElement):
        return htmlobject
    # do not accept any other type after this point
    if not isinstance(htmlobject, (bytes, str)):
        raise TypeError("incompatible input type: %s", type(htmlobject))
    # the string is a URL, download it
    if isinstance(htmlobject, str) and htmlobject.startswith("http"):
        htmltext = None
        if re.match(r"https?://[^ ]+$", htmlobject):
            LOGGER.info("URL detected, downloading: %s", htmlobject)
            htmltext = fetch_url(htmlobject)
            if htmltext is not None:
                htmlobject = htmltext
        # log the error and quit
        if htmltext is None:
            raise ValueError("URL couldn't be processed: %s", htmlobject)
    # start processing
    tree = None
    # try to guess encoding and decode file: if None then keep original
    htmlobject = decode_file(htmlobject)
    # sanity check
    check_flag = is_dubious_html(htmlobject)
    # use Unicode string
    try:
        tree = fromstring(htmlobject, parser=HTML_PARSER)
    except ValueError:
        # "Unicode strings with encoding declaration are not supported."
        try:
            tree = fromstring(htmlobject.encode("utf8"), parser=HTML_PARSER)
        except Exception as err:
            LOGGER.error("lxml parser bytestring %s", err)
    except Exception as err:
        LOGGER.error("lxml parsing failed: %s", err)
    # rejection test: is it (well-formed) HTML at all?
    if tree is not None and check_flag is True and len(tree) < 2:
        LOGGER.error(
            "parsed tree length: %s, wrong data type or not valid HTML", len(tree)
        )
        tree = None
    return tree

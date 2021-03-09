# pylint:disable-msg=E0611,I1101
"""
Module bundling functions related to HTML processing.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license


# standard
import logging
import re
import urllib3

# CChardet is faster and can be more accurate
try:
    import cchardet as chardet
except ImportError:
    import chardet

from lxml import etree, html

from .settings import MAX_FILE_SIZE, MIN_FILE_SIZE


LOGGER = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
RETRY_STRATEGY = urllib3.util.Retry(
    total=3,
    connect=0,
    status_forcelist=[429, 500, 502, 503, 504],
)
HTTP_POOL = urllib3.PoolManager(retries=RETRY_STRATEGY)

HTML_PARSER = html.HTMLParser(remove_comments=True, remove_pis=True, encoding='utf-8')
RECOVERY_PARSER = html.HTMLParser(remove_comments=True, remove_pis=True)


def isutf8(data):
    """Simple heuristic to determine if a bytestring uses standard unicode encoding"""
    try:
        data.decode('UTF-8')
    except UnicodeDecodeError:
        return False
    else:
        return True


def detect_encoding(bytesobject):
    """Read the first chunk of input and return its encoding"""
    # unicode-test
    if isutf8(bytesobject):
        return 'UTF-8'
    # try one of the installed detectors
    guess = chardet.detect(bytesobject)
    LOGGER.debug('guessed encoding: %s', guess['encoding'])
    return guess['encoding']


def decode_response(response):
    """Read the urllib3 object corresponding to the server response,
       try to guess its encoding and decode it to return a unicode string"""
    if isinstance(response, bytes):
        resp_content = response
    else:
        resp_content = response.data
    guessed_encoding = detect_encoding(resp_content)
    LOGGER.debug('response encoding: %s', guessed_encoding)
    # process
    htmltext = None
    if guessed_encoding is not None:
        try:
            htmltext = resp_content.decode(guessed_encoding)
        except UnicodeDecodeError:
            LOGGER.warning('encoding error: %s', guessed_encoding)
    # force decoding # ascii instead?
    if htmltext is None:
        htmltext = str(resp_content, encoding='utf-8', errors='replace')
    return htmltext


def fetch_url(url):
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
        response = HTTP_POOL.request('GET', url, timeout=30)
    except urllib3.exceptions.NewConnectionError as err:
        LOGGER.error('connection refused: %s %s', url, err)
    except urllib3.exceptions.MaxRetryError as err:
        LOGGER.error('retries/redirects: %s %s', url, err)
    except urllib3.exceptions.TimeoutError as err:
        LOGGER.error('connection timeout: %s %s', url, err)
    except Exception as err:
        logging.error('unknown error: %s %s', url, err) # sys.exc_info()[0]
    else:
        # safety checks
        if response.status != 200:
            LOGGER.error('not a 200 response: %s for URL %s', response.status, url)
        elif response.data is None or len(response.data) < MIN_FILE_SIZE:
            LOGGER.error('too small/incorrect for URL %s', url)
        elif len(response.data) > MAX_FILE_SIZE:
            LOGGER.error('too large: length %s for URL %s', len(response.data), url)
        else:
            return decode_response(response.data)
    return None


def load_html(htmlobject):
    """Load object given as input and validate its type.
    Accepted: LXML tree, bytestring and string (HTML document or URL).
    Raises ValueError if a URL is passed without result.
    """
    # use tree directly
    if isinstance(htmlobject, (etree._ElementTree, html.HtmlElement)):
        return htmlobject
    tree = None
    check_flag = False
    # try to detect encoding and convert to string
    if isinstance(htmlobject, bytes):
        # test
        if 'html' not in htmlobject[:50].decode(encoding='ascii', errors='ignore').lower():
            check_flag = True
        guessed_encoding = detect_encoding(htmlobject)
        if guessed_encoding is not None:
            if guessed_encoding == 'UTF-8':
                tree = html.fromstring(htmlobject, parser=HTML_PARSER)
            else:
                try:
                    htmlobject = htmlobject.decode(guessed_encoding)
                    tree = html.fromstring(htmlobject, parser=HTML_PARSER)
                except (LookupError, UnicodeDecodeError):  # VISCII encoding
                    LOGGER.warning('encoding issue: %s', guessed_encoding)
                    tree = html.fromstring(htmlobject, parser=RECOVERY_PARSER)
        else:
            tree = html.fromstring(htmlobject, parser=RECOVERY_PARSER)
    # use string if applicable
    elif isinstance(htmlobject, str):
        # the string is a URL, download it
        if htmlobject.startswith('http'):
            htmltext = None
            if re.match(r'https?://[^ ]+$', htmlobject):
                LOGGER.info('URL detected, downloading: %s', htmlobject)
                htmltext = fetch_url(htmlobject)
                if htmltext is not None:
                    htmlobject = htmltext
            # log the error and quit
            if htmltext is None:
                raise ValueError("URL couldn't be processed: %s", htmlobject)
        # test
        if 'html' not in htmlobject[:50].lower():
            check_flag = True
        try:
            tree = html.fromstring(htmlobject, parser=HTML_PARSER)
        except ValueError:
            # try to parse a bytestring
            try:
                tree = html.fromstring(htmlobject.encode('utf8'), parser=HTML_PARSER)
            except Exception as err:
                LOGGER.error('parser bytestring %s', err)
        except Exception as err:
            LOGGER.error('parsing failed: %s', err)
    # default to None
    else:
        LOGGER.error('this type cannot be processed: %s', type(htmlobject))
    # further test: is it (well-formed) HTML at all?
    if tree is not None and check_flag is True:
        if len(tree) < 2:
            LOGGER.error('parsed tree length: %s, wrong data type or not valid HTML', len(tree))
            tree = None
    return tree

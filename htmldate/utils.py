# pylint:disable-msg=E0611,I1101
"""
Module bundling functions related to HTML processing.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license


# standard
import logging
import re
import socket
import urllib3

try:
    # this module is faster
    import cchardet
except ImportError:
    cchardet = None

import requests
from lxml import etree, html

from .settings import MAX_FILE_SIZE, MIN_FILE_SIZE


LOGGER = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    if cchardet is not None:
        guess = cchardet.detect(bytesobject)
        LOGGER.debug('guessed encoding: %s', guess['encoding'])
        return guess['encoding']
    return None


def decode_response(response):
    """Read the first chunk of server response and decode it"""
    guessed_encoding = detect_encoding(response.content)
    LOGGER.debug('response/guessed encoding: %s / %s', response.encoding, guessed_encoding)
    # process
    if guessed_encoding is not None:
        try:
            htmltext = response.content.decode(guessed_encoding)
        except UnicodeDecodeError:
            LOGGER.warning('encoding error: %s / %s', response.encoding, guessed_encoding)
            htmltext = response.text
    else:
        htmltext = response.text
    return htmltext


def fetch_url(url):
    """ Fetch page using requests/urllib3
    Args:
        URL: URL of the page to fetch
    Returns:
        request object (headers + body).
    Raises:
        Nothing.
    """
    # customize headers
    headers = {
        'Connection': 'close',  # another way to cover tracks
        # 'User-Agent': '',  # your string here
    }
    # send
    try:
        # read by streaming chunks (stream=True, iter_content=xx)
        # so we can stop downloading as soon as MAX_FILE_SIZE is reached
        response = requests.get(url, timeout=30, verify=False, allow_redirects=True,
                                headers=headers)
    except (requests.exceptions.MissingSchema, requests.exceptions.InvalidURL):
        LOGGER.error('malformed URL: %s', url)
    except requests.exceptions.TooManyRedirects:
        LOGGER.error('redirects: %s', url)
    except requests.exceptions.SSLError as err:
        LOGGER.error('SSL: %s %s', url, err)
    except (socket.timeout, requests.exceptions.ConnectionError,
            requests.exceptions.Timeout, socket.error, socket.gaierror) as err:
        LOGGER.error('connection: %s %s', url, err)
    # except Exception as err:
    #    logging.error('unknown: %s %s', url, err) # sys.exc_info()[0]
    else:
        # safety checks
        if response.status_code != 200:
            LOGGER.error('not a 200 response: %s', response.status_code)
        elif response.text is None or len(response.text) < MIN_FILE_SIZE:
            LOGGER.error('too small/incorrect: %s %s', url, len(response.text))
        elif len(response.text) > MAX_FILE_SIZE:
            LOGGER.error('too large: %s %s', url, len(response.text))
        else:
            return decode_response(response)
    return None


def load_html(htmlobject):
    """Load object given as input and validate its type.
    Accepted: LXML tree, bytestring and string (HTML document or URL)
    """
    tree = None
    # use tree directly
    if isinstance(htmlobject, (etree._ElementTree, html.HtmlElement)):
        return htmlobject
    # try to detect encoding and convert to string
    if isinstance(htmlobject, bytes):
        guessed_encoding = detect_encoding(htmlobject)
        if guessed_encoding is not None:
            if guessed_encoding == 'UTF-8':
                tree = html.fromstring(htmlobject, parser=HTML_PARSER)
            else:
                try:
                    htmlobject = htmlobject.decode(guessed_encoding)
                    tree = html.fromstring(htmlobject, parser=HTML_PARSER)
                except UnicodeDecodeError:
                    LOGGER.warning('encoding issue: %s', guessed_encoding)
                    tree = html.fromstring(htmlobject, parser=RECOVERY_PARSER)
        else:
            tree = html.fromstring(htmlobject, parser=RECOVERY_PARSER)
    # use string if applicable
    if isinstance(htmlobject, str):
        # the string is a URL, download it
        if re.search(r'^https?://[^ ]+$', htmlobject):
            LOGGER.info('URL detected, downloading: %s', htmlobject)
            htmltext = fetch_url(htmlobject)
            if htmltext is not None:
                htmlobject = htmltext
            else:
                return None
        # robust parsing
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
    return tree

# -*- coding: utf-8 -*-
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
from io import StringIO # Python 3

# libraries
import cchardet as chardet
import requests
from lxml import etree, html


LOGGER = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# LXML
HTML_PARSER = html.HTMLParser() # encoding='utf8'



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
    headers = requests.utils.default_headers()
    headers.update({
        'Connection': 'close',  # another way to cover tracks
        # 'User-Agent': '', # your string here
    })
    # send
    try:
        response = requests.get(url, timeout=30, verify=False, allow_redirects=True, headers=headers)
    except (requests.exceptions.MissingSchema, requests.exceptions.InvalidURL):
        LOGGER.error('malformed URL: %s', url)
    except requests.exceptions.TooManyRedirects:
        LOGGER.error('redirects: %s', url)
    except requests.exceptions.SSLError as err:
        LOGGER.error('SSL: %s %s', url, err)
    except (socket.timeout, requests.exceptions.ConnectionError, requests.exceptions.Timeout, socket.error, socket.gaierror) as err:
        LOGGER.error('connection: %s %s', url, err)
    #except Exception as err:
    #    logging.error('unknown: %s %s', url, err) # sys.exc_info()[0]
    # if no error
    else:
        # safety checks
        if int(response.status_code) != 200:
            LOGGER.error('not a 200 response: %s', response.status_code)
        elif response.text is None or len(response.text) < 100:
            LOGGER.error('file too small/incorrect response: %s %s', url, len(response.text))
        elif len(response.text) > 20000000:
            LOGGER.error('file too large: %s %s', url, len(response.text))
        else:
            guessed_encoding = chardet.detect(response.content)['encoding']
            LOGGER.debug('response/guessed encoding: %s / %s', response.encoding, guessed_encoding)
            if guessed_encoding is not None:
                try:
                    htmltext = response.content.decode(guessed_encoding)
                except UnicodeDecodeError:
                    htmltext = response.text
            else:
                htmltext = response.text
            # return here
            return htmltext
    # catchall
    return None


#@profile
def load_html(htmlobject):
    """Load object given as input and validate its type (accepted: LXML tree and string, HTML document or URL)"""
    if isinstance(htmlobject, (etree._ElementTree, html.HtmlElement)):
        # copy tree
        tree = htmlobject
    elif isinstance(htmlobject, str):
        # the string is a URL, download it
        if re.search(r'^https?://[^ ]+$', htmlobject):
            LOGGER.info('URL detected, downloading: %s', htmlobject)
            htmltext = fetch_url(htmlobject)
            if htmltext is not None:
                htmlobject = htmltext
            else:
                return None
        ## robust parsing
        try:
            # parse
            tree = html.parse(StringIO(htmlobject), parser=HTML_PARSER)
            # tree = html.fromstring(html.encode('utf8'), parser=parser)
        except UnicodeDecodeError as err:
            LOGGER.error('unicode %s', err)
            tree = None
        except UnboundLocalError as err:
            LOGGER.error('parsed string %s', err)
            tree = None
        except (etree.XMLSyntaxError, ValueError, AttributeError) as err:
            LOGGER.error('parser %s', err)
            tree = None
    else:
        LOGGER.error('this type cannot be processed: %s', type(htmlobject))
        tree = None
    return tree

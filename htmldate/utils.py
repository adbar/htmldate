# -*- coding: utf-8 -*-
"""
Module bundling functions related to HTML processing.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license


# standard
import logging
import socket
import re
import urllib3

# libraries
import requests

from io import StringIO # Python 3
from lxml import etree, html


logger = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# LXML
HTML_PARSER = html.HTMLParser() # encoding='utf8'



def fetch_url(url): # custombool?
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
        rget = requests.get(url, timeout=30, verify=False, allow_redirects=True, headers=headers)
    except (requests.exceptions.MissingSchema, requests.exceptions.InvalidURL):
        logging.error('malformed URL: %s', url)
    except requests.exceptions.TooManyRedirects:
        logging.error('redirects: %s', url)
    except requests.exceptions.SSLError as err:
        logging.error('SSL: %s %s', url, err)
    except (socket.timeout, requests.exceptions.ConnectionError, requests.exceptions.Timeout, socket.error, socket.gaierror) as err:
        logging.error('connection: %s %s', url, err)
    #except Exception as err:
    #    logging.error('unknown: %s %s', url, err) # sys.exc_info()[0]
    # if no error
    else:
        # safety checks
        if int(rget.status_code) != 200:
            logging.error('not a 200 response: %s', rget.status_code)
        elif rget.text is None or len(rget.text) < 100:
            logging.error('file too small/incorrect response: %s %s', url, len(rget.text))
        elif len(rget.text) > 20000000:
            logging.error('file too large: %s %s', url, len(rget.text))
        else:
            return rget.text
    # catchall
    return None


#@profile
def load_html(htmlobject):
    """Load object given as input and validate its type (accepted: LXML tree and string)"""
    if isinstance(htmlobject, (etree._ElementTree, html.HtmlElement)):
        # copy tree
        tree = htmlobject
        # derive string
        htmlstring = html.tostring(htmlobject, encoding='unicode')
    elif isinstance(htmlobject, str):
        # the string is a URL, download it
        if re.match(r'https?://', htmlobject):
            logger.info('URL detected, downloading: %s', htmlobject)
            htmltext = fetch_url(htmlobject)
            if htmltext is not None:
                htmlstring = htmltext
        # copy string
        else:
            htmlstring = htmlobject
        ## robust parsing
        try:
            # parse
            tree = html.parse(StringIO(htmlstring), parser=HTML_PARSER)
            # tree = html.fromstring(html.encode('utf8'), parser=parser)
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

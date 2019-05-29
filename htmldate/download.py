# -*- coding: utf-8 -*-
"""
Download web pages.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license

# standard
import logging
import socket
import urllib3

# libraries
import requests



## INIT
logger = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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

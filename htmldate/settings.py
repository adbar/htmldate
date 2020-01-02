#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Listing a series of settings that are applied module-wide.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license

import datetime

# dateparser module
try:
    import dateparser # third-party, slow
    EXTERNAL_PARSER = dateparser.DateDataParser(settings={'PREFER_DAY_OF_MONTH': 'first', 'PREFER_DATES_FROM': 'past', 'DATE_ORDER': 'DMY'})
    # allow_redetect_language=False,
    # languages=['de', 'en'],
    EXTERNAL_PARSER_CONFIG = {'PREFER_DAY_OF_MONTH': 'first', 'PREFER_DATES_FROM': 'past', 'DATE_ORDER': 'DMY'}
except ImportError:
    EXTERNAL_PARSER = None
    EXTERNAL_PARSER_CONFIG = None

# Download
MAX_FILE_SIZE = 20000000
MIN_FILE_SIZE = 10

## Plausible dates
# earliest possible year to take into account (inclusive)
MIN_YEAR = 1995
# latest possible date
LATEST_POSSIBLE = datetime.date.today()
# latest possible year
MAX_YEAR = datetime.date.today().year

# try dateutil parser
DEFAULT_PARSER_PARAMS = {'dayfirst': True, 'fuzzy': False}

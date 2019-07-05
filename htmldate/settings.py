#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Listing a series of settings that are applied module-wide.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license

import datetime
import dateparser # third-party, slow


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

# dateparser module
PARSERCONFIG = {'PREFER_DAY_OF_MONTH': 'first', 'PREFER_DATES_FROM': 'past', 'DATE_ORDER': 'DMY'}
PARSER = dateparser.DateDataParser(settings={'PREFER_DAY_OF_MONTH': 'first', 'PREFER_DATES_FROM': 'past', 'DATE_ORDER': 'DMY'}) # allow_redetect_language=False, # languages=['de', 'en'], 

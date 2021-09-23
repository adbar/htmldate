# pylint:disable-msg=E0611
"""
Listing a series of settings that are applied module-wide.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license

import datetime

from lxml.html.clean import Cleaner


# Function cache
CACHE_SIZE = 8192

# Download
MAX_FILE_SIZE = 20000000
MIN_FILE_SIZE = 10

# Plausible dates
# earliest possible year to take into account (inclusive)
MIN_DATE = datetime.date(1995, 1, 1)
MIN_YEAR = MIN_DATE.year
# latest possible date
LATEST_POSSIBLE = datetime.date.today()
# latest possible year
MAX_YEAR = LATEST_POSSIBLE.year

# set an upper limit to the number of candidates
MAX_POSSIBLE_CANDIDATES = 150

# HTML_CLEANER config # http://lxml.de/api/lxml.html.clean.Cleaner-class.html
HTML_CLEANER = Cleaner()
HTML_CLEANER.comments = False
HTML_CLEANER.embedded = True
HTML_CLEANER.forms = False
HTML_CLEANER.frames = True
HTML_CLEANER.javascript = True
HTML_CLEANER.links = False
HTML_CLEANER.meta = False
HTML_CLEANER.page_structure = True
HTML_CLEANER.processing_instructions = True
HTML_CLEANER.remove_unknown_tags = False
HTML_CLEANER.safe_attrs_only = False
HTML_CLEANER.scripts = False
HTML_CLEANER.style = True
HTML_CLEANER.kill_tags = ['applet', 'audio', 'canvas', 'datalist', 'embed',
                          'figure', 'label', 'map', 'math', 'object',
                          'picture', 'rdf', 'svg', 'video']

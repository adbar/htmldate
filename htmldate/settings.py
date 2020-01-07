# pylint:disable-msg=E0611
"""
Listing a series of settings that are applied module-wide.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license

import datetime

from lxml.html.clean import Cleaner

# Download
MAX_FILE_SIZE = 20000000
MIN_FILE_SIZE = 10

# Plausible dates
# earliest possible year to take into account (inclusive)
MIN_YEAR = 1995
# latest possible date
LATEST_POSSIBLE = datetime.date.today()
# latest possible year
MAX_YEAR = datetime.date.today().year

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
HTML_CLEANER.kill_tags = ['audio', 'canvas', 'label', 'map', 'math', 'object',
                          'picture', 'rdf', 'svg', 'video']
# 'embed', 'figure', 'img', 'table'

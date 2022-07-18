# pylint:disable-msg=E0611
"""
Listing a series of settings that are applied module-wide.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license

from datetime import datetime

from lxml.html.clean import Cleaner  # type: ignore


# Function cache
CACHE_SIZE: int = 8192

# Download
MAX_FILE_SIZE: int = 20000000
MIN_FILE_SIZE: int = 10

# Plausible dates
# earliest possible year to take into account (inclusive)
MIN_DATE: datetime = datetime(1995, 1, 1)
MIN_YEAR: int = MIN_DATE.year
# latest possible date
LATEST_POSSIBLE: datetime = datetime.now()
# latest possible year
MAX_YEAR: int = LATEST_POSSIBLE.year

# set an upper limit to the number of candidates
MAX_POSSIBLE_CANDIDATES: int = 1000

# HTML_CLEANER config
# https://lxml.de/api/lxml.html.clean.Cleaner-class.html
# https://lxml.de/apidoc/lxml.html.clean.html
HTML_CLEANER: Cleaner = Cleaner(
    annoying_tags=False,
    comments=False,
    embedded=True,  # affects recall?
    forms=False,
    frames=True,
    javascript=False,
    links=False,
    meta=False,
    page_structure=True,
    processing_instructions=False,
    remove_unknown_tags=False,
    safe_attrs_only=False,
    scripts=False,
    style=False,
    kill_tags=[
        "applet",
        "audio",
        "canvas",
        "datalist",
        "embed",
        "figure",
        "label",
        "map",
        "math",
        "object",
        "picture",
        "rdf",
        "svg",
        "video",
    ],
)

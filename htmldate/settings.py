# pylint:disable-msg=E0611
"""
Listing a series of settings that are applied module-wide.
"""

from datetime import datetime

#: Number of parsed date expressions kept in the cache
CACHE_SIZE: int = 8192

#: Maximum size of a download or of command-line input, larger ones are rejected
MAX_FILE_SIZE: int = 20000000

#: Earliest date taken into account (inclusive), default of ``min_date``
MIN_DATE: datetime = datetime(1995, 1, 1)

#: Maximum number of date candidates of one kind, more are deemed implausible
MAX_POSSIBLE_CANDIDATES: int = 1000

#: Text segments up to this length are not parsed for dates (in characters)
MIN_SEGMENT_LEN: int = 6

#: Length limit of text segments parsed for dates, longer ones are cut or skipped
MAX_SEGMENT_LEN: int = 52

#: Elements removed before the page structure and text are searched
CLEANING_LIST = [
    "applet",
    "audio",
    "canvas",
    "datalist",
    "embed",
    "frame",
    "frameset",
    "iframe",
    "label",
    "map",
    "math",
    "noframes",
    "object",
    "picture",
    "rdf",
    "svg",
    "track",
    "video",
]
# "figure", "input", "layer", "param", "source"

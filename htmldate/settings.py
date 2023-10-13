# pylint:disable-msg=E0611
"""
Listing a series of settings that are applied module-wide.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license

from datetime import datetime

# Function cache
CACHE_SIZE: int = 8192

# Download
MAX_FILE_SIZE: int = 20000000
MIN_FILE_SIZE: int = 10

# Plausible dates
# earliest possible date to take into account (inclusive)
MIN_DATE: datetime = datetime(1995, 1, 1)

# set an upper limit to the number of candidates
MAX_POSSIBLE_CANDIDATES: int = 1000

CLEANING_LIST = [
    "applet",
    "audio",
    "canvas",
    "datalist",
    "embed",
    "frame",
    "frameset",
    "figure",
    "label",
    "map",
    "math",
    "noframes",
    "object",
    "picture",
    "rdf",
    "svg",
    "video",
]
# "iframe", "layer", "param"

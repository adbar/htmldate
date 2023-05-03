"""
Htmldate extracts original and updated publication dates from URLs and web pages.
"""

# meta
__title__ = "htmldate"
__author__ = "Adrien Barbaresi"
__license__ = "GNU GPL v3"
__copyright__ = "Copyright 2017-2023, Adrien Barbaresi"
__version__ = "1.4.3"


import logging
from datetime import datetime

try:
    datetime.fromisoformat  # type: ignore[attr-defined]
except AttributeError:  # Python 3.6
    from backports.datetime_fromisoformat import MonkeyPatch  # type: ignore

    MonkeyPatch.patch_fromisoformat()

from .core import find_date

logging.getLogger(__name__).addHandler(logging.NullHandler())

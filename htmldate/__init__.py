"""
Htmldate extracts original and updated publication dates from URLs and web pages.
"""

# meta
__title__ = "htmldate"
__author__ = "Adrien Barbaresi"
__license__ = "GNU GPL v3"
__copyright__ = "Copyright 2017-2023, Adrien Barbaresi"
__version__ = "1.5.0"


import logging

from sys import version_info

from .core import find_date


if version_info.minor < 11:
    from backports.datetime_fromisoformat import MonkeyPatch  # type: ignore

    MonkeyPatch.patch_fromisoformat()

logging.getLogger(__name__).addHandler(logging.NullHandler())

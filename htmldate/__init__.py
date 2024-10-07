"""
Htmldate extracts original and updated publication dates from URLs and web pages.
"""

# meta
__title__ = "htmldate"
__author__ = "Adrien Barbaresi"
__license__ = "Apache-2.0"
__copyright__ = "Copyright 2017-2024, Adrien Barbaresi"
__version__ = "1.9.1"


import logging

from datetime import datetime

from .core import find_date

logging.getLogger(__name__).addHandler(logging.NullHandler())

"""
Extract the date of web pages, or web archeology in practice.
"""

# meta
__title__ = 'htmldate'
__author__ = 'Adrien Barbaresi'
__license__ = 'GNU GPL v3'
__copyright__ = 'Copyright 2017-2020, Adrien Barbaresi'
__version__ = '0.6.3'


import logging

from .core import find_date

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass
logging.getLogger(__name__).addHandler(NullHandler())

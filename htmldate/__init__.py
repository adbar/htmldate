"""
Extract the date of web pages, or web archeology in practice.
"""

# meta
__title__ = 'htmldate'
__author__ = 'Adrien Barbaresi'
__license__ = 'GNU GPL v3'
__copyright__ = 'Copyright 2017-2022, Adrien Barbaresi'
__version__ = '1.0.0'


import logging

from .core import find_date

logging.getLogger(__name__).addHandler(logging.NullHandler())

# -*- coding: utf-8 -*-
"""
Extract the date of web pages, or web archeology in practice.
"""


__title__ = 'htmldate'
__author__ = 'Adrien Barbaresi'
__license__ = 'GNU GPL v3'
__copyright__ = 'Copyright 2017, Adrien Barbaresi'
__version__ = '0.1.2'


from .core import *


# logging best practices # http://docs.python-guide.org/en/latest/writing/logging/
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

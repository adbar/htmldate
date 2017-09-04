# -*- coding: utf-8 -*-
"""
Implementing a basic command-line interface.
"""

import sys

from htmldate import find_date


def main():
    htmlstring = sys.stdin.read()
    # safety check
    if len(htmlstring) > 10000000:
        print ('# ERROR: file too large')
    elif len(htmlstring) < 10:
        print ('# ERROR: file too small')
    # proceed
    else:
        result = find_date(htmlstring)
        print(result)

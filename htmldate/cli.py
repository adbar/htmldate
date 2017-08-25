# -*- coding: utf-8 -*-
"""
Implementing a basic command-line interface.
"""

import sys

from htmldate import find_date


def main():
    htmlstring = sys.stdin.read()
    result = find_date(htmlstring)
    print(result)

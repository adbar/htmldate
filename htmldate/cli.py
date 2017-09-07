# -*- coding: utf-8 -*-
"""
Implementing a basic command-line interface.
"""

import sys

from htmldate import find_date


def main():
    """ Run as a command-line utility. """
    # unicode check
    try:
        htmlstring = sys.stdin.read()
    except UnicodeDecodeError as err:
        sys.stderr.write('# ERROR: system/buffer encoding:' + str(err) + '\n')
        sys.exit(1)

    # safety check
    if len(htmlstring) > 10000000:
        sys.stderr.write('# ERROR: file too large\n')
    elif len(htmlstring) < 10:
        sys.stderr.write('# ERROR: file too small\n')
    # proceed
    else:
        result = find_date(htmlstring)
        if result:
            sys.stdout.write(result + '\n')



if __name__ == '__main__':
    main()

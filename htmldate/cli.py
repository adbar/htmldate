# -*- coding: utf-8 -*-
"""
Implementing a basic command-line interface.
"""

import argparse
import logging
import sys

from htmldate import find_date



def main():
    """ Run as a command-line utility. """
    # arguments
    argsparser = argparse.ArgumentParser()
    argsparser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    argsparser.add_argument("-s", "--safe", help="safe mode: markup search only", action="store_true")
    args = argsparser.parse_args()

    if args.verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

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
        if args.safe:
            result = find_date(htmlstring, False)
        else:
            result = find_date(htmlstring)
        if result:
            sys.stdout.write(result + '\n')



if __name__ == '__main__':
    main()

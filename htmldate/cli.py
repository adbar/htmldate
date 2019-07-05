# -*- coding: utf-8 -*-
"""
Implementing a basic command-line interface.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license

import argparse
import logging
import sys

from .core import find_date
from .utils import fetch_url


def examine(htmlstring, extensive_bool=True, original_date=False):
    """ Generic safeguards and triggers """
    # safety check
    if htmlstring is None:
        sys.stderr.write('# ERROR: empty document\n')
    elif len(htmlstring) > 10000000:
        sys.stderr.write('# ERROR: file too large\n')
    elif len(htmlstring) < 10:
        sys.stderr.write('# ERROR: file too small\n')
    # proceed
    else:
        result = find_date(htmlstring, extensive_bool, original_date)
        return result
    return None


def main():
    """ Run as a command-line utility. """
    # arguments
    argsparser = argparse.ArgumentParser()
    argsparser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    argsparser.add_argument("-f", "--fast", help="fast mode: disable extensive search", action="store_false")
    argsparser.add_argument("--original", help="original date prioritized", action="store_true")
    argsparser.add_argument("-i", "--inputfile", help="name of input file for batch processing (similar to wget -i)", type=str)
    argsparser.add_argument("-u", "--URL", help="custom URL download", type=str)
    args = argsparser.parse_args()

    if args.verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    # process input on STDIN
    if not args.inputfile:
        # URL as input
        if args.URL:
            htmlstring = fetch_url(args.URL)
            if htmlstring is None:
                sys.exit('# ERROR no valid result for url: ' + args.URL + '\n') # exit code: 1
        # unicode check
        else:
            try:
                htmlstring = sys.stdin.read()
            except UnicodeDecodeError as err:
                # input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='latin-1')
                sys.exit('# ERROR system/buffer encoding: ' + str(err) + '\n') # exit code: 1

        result = examine(htmlstring, args.fast, args.original)
        if result is not None:
            sys.stdout.write(result + '\n')

    # process input file line by line
    else:
        with open(args.inputfile, mode='r', encoding='utf-8') as inputfile: # errors='strict', buffering=1
            for line in inputfile:
                htmltext = fetch_url(line.strip())
                result = examine(htmltext, args.fast, args.original)
                if result is None:
                    result = 'None'
                sys.stdout.write(line.strip() + '\t' + result + '\n')


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""
Implementing a basic command-line interface.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license

import argparse
import logging
import sys

from codecs import open # python2

from htmldate import find_date, fetch_url



def examine(htmlstring, safebool):
    """ Generic safeguards and triggers """
    # safety check
    if len(htmlstring) > 1000000:
        sys.stderr.write('# ERROR: file too large\n')
    elif len(htmlstring) < 10:
        sys.stderr.write('# ERROR: file too small\n')
    # proceed
    else:
        if safebool:
            result = find_date(htmlstring, extensive_search=False)
        else:
            result = find_date(htmlstring)
        return result
    return None



def main():
    """ Run as a command-line utility. """
    # arguments
    argsparser = argparse.ArgumentParser()
    argsparser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    argsparser.add_argument("-s", "--safe", help="safe mode: markup search only", action="store_true")
    argsparser.add_argument("-i", "--inputfile", help="name of input file for batch processing (similar to wget -i)")
    args = argsparser.parse_args()

    if args.verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    # process input on STDIN
    if not args.inputfile:
        # unicode check
        try:
            htmlstring = sys.stdin.read()
        except UnicodeDecodeError as err:
            sys.stderr.write('# ERROR system/buffer encoding: ' + str(err) + '\n')
            sys.exit(1)

        result = examine(htmlstring, args.safe)
        if result is not None:
            sys.stdout.write(result + '\n')

    # process input file line by line
    else:
        with open(args.inputfile, 'r', 'utf-8') as inputfile:
            for line in inputfile:
                url = line.strip()
                rget = fetch_url(url)
                if rget is not None:
                    result = examine(rget.text, args.safe)
                    # if result is not None:
                    sys.stdout.write(result + '\t' + url + '\n')



if __name__ == '__main__':
    main()

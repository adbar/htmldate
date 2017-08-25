# -*- coding: utf-8 -*-
"""
Module bundling all needed functions.
"""

## This file is available from https://github.com/adbar/htmldate
## under GNU GPL v3 license


# Noteworthy sources
# https://github.com/ianstormtaylor/metascraper/blob/master/lib/rules/date.js
# https://github.com/grangier/python-goose/blob/develop/goose/extractors/publishdate.py
# https://github.com/codelucas/newspaper/blob/master/newspaper/extractors.py


# compatibility
from __future__ import print_function, unicode_literals

# standard
import datetime
import re

from collections import defaultdict
from io import StringIO # python3

# third-party
import dateparser
from lxml import etree, html

# own
# import settings



DATE_EXPRESSIONS = ["//*[starts-with(@id, 'date')]", "//*[starts-with(@class, 'date')]", "//*[starts-with(@class, 'byline')]", "//*[starts-with(@class, 'entry-date')]", "//*[starts-with(@class, 'post-meta')]", "//*[starts-with(@class, 'postmetadata')]"]

OUTPUTFORMAT = '%Y-%m-%d'


def date_validator(datestring):
    """Validate a string with respect to the chosen outputformat and basic heuristics"""
    # try if date can be parsed using chosen outputformat
    try:
        dateobject = datetime.datetime.strptime(datestring, OUTPUTFORMAT)
    except ValueError:
        return False
    # basic year validation
    year = int(datetime.date.strftime(dateobject, '%Y'))
    if 1995 < year < 2020:
        return True
    return False




def try_date(string):
    """Use dateparser to parse the assumed date expression"""
    target = dateparser.parse(string, settings={'PREFER_DAY_OF_MONTH': 'first', 'PREFER_DATES_FROM': 'past', 'DATE_ORDER': 'DMY'})
    if target is not None:
        datestring = datetime.date.strftime(target, OUTPUTFORMAT)
        if date_validator(datestring) is True:
            return datestring
    return None



def examine_date_elements(tree, expression):
    """Check HTML elements one by one for date expressions"""
    elements = tree.xpath(expression)
    if elements is not None:
        for elem in elements:
            # simple length heuristics
            if 3 < len(elem.text_content().strip()) < 30:
                print('# DEBUG analyzing:', html.tostring(elem, pretty_print=False, encoding='unicode'), elem.text_content().strip())
                attempt = try_date(elem.text_content().strip())
                if attempt is not None:
                    print('# DEBUG result:', attempt)
                    if date_validator(attempt) is True:
                        return attempt
    return None



def examine_header(tree):
    """Parse header elements to find date cues"""
    headerdate = None
    # meta elements in header
    try:
        for elem in tree.xpath('//head/meta'):
            # safeguard
            if len(elem.attrib) < 1:
                continue
            ## property attribute
            if elem.get('property') is not None:
                # safeguard
                if elem.get('content') is None or len(elem.get('content')) < 1:
                    continue
                # "og:" for OpenGraph http://ogp.me/
                if elem.get('property') == 'og:article:published_time':
                    if headerdate is None:
                        attempt = try_date(elem.get('content'))
                        if attempt is not None:
                            headerdate = attempt
                else:
                    # time
                    if elem.get('property') in ('article:published_time', 'dc:created', 'dc:date', 'rnews:datePublished'):
                        if headerdate is None:
                            attempt = try_date(elem.get('content'))
                            if attempt is not None:
                                headerdate = attempt
            # name attribute
            elif 'name' in elem.attrib: # elem.get('name') is not None:
                # safeguard
                if elem.get('content') is None or len(elem.get('content')) < 1:
                    continue
                # date
                elif elem.get('name') in ('article_date_original', 'date', 'dc.date', 'dc.date.created', 'dc.date.issued', 'dcterms.date', 'gentime', 'og:published_time', 'originalpublicationdate', 'publishdate', 'publication_date', 'sailthru.date'):
                    if headerdate is None:
                        attempt = try_date(elem.get('content'))
                        if attempt is not None:
                            headerdate = attempt
            # other types
            else:
                if elem.get('itemprop') in ('datepublished', 'pubyear') or elem.get('pubdate') == 'pubdate': # itemscope?
                    if elem.get('datetime') is not None and len(elem.get('datetime')) > 1:
                        if headerdate is None:
                            attempt = try_date(elem.get('content'))
                            if attempt is not None:
                                headerdate = attempt

    except etree.XPathEvalError as err:
        print('# ERROR: XPath', err)
        return None

    if headerdate is not None and date_validator(headerdate) is True:
        return headerdate
    return None




def search_pattern(htmlstring, pattern):
    """Search the given regex pattern throughout the document and return the most frequent match"""
    dic = defaultdict(int)
    try:
        for expression in re.findall(r'%s' % pattern, htmlstring):
            dic[expression] += 1
        vals = list(dic.values())
        k = list(dic.keys())
        if len(vals) > 0:
            return k[vals.index(max(vals))]
    except UnboundLocalError:
        pass
    return None


def search_page(htmlstring):
    """Search the page for common patterns (can be dangerous!)"""
    # init
    pagedate = None

    # date ultimate rescue for the rest: most frequent year/month comination in the HTML
    ## this is risky

    # 1
    mostfrequent = search_pattern(htmlstring, '/([0-9]{4}/[0-9]{2})/')
    if mostfrequent is not None:
        match = re.match(r'([0-9]{4})/([0-9]{2})', mostfrequent)
        if match:
            pagedate = '-'.join([match.group(1), match.group(2), '01'])
            if date_validator(pagedate) is True:
                return pagedate

    # 2
    mostfrequent = search_pattern(htmlstring, '\D([0-9]{2}[/.][0-9]{4})\D')
    if mostfrequent is not None:
        match = re.match(r'([0-9]{2})[/.]([0-9]{4})', mostfrequent)
        if match:
            pagedate = '-'.join([match.group(2), match.group(1), '01'])
            if date_validator(pagedate) is True:
                return pagedate

    # last try
    mostfrequent = search_pattern(htmlstring, '\D(2[01][0-9]{2})\D')
    if mostfrequent is not None:
        pagedate = '-'.join([mostfrequent, '07', '01'])
        if date_validator(pagedate) is True:
            return pagedate

    return None



def find_date(htmlstring):
    """Main function: apply a series of techniques to date the document, from safe to adventurous"""
    # init
    pagedate = None

    # robust parsing
    try:
        tree = html.parse(StringIO(htmlstring), html.HTMLParser())
    except (etree.XMLSyntaxError, ValueError, AttributeError) as err:
        print('ERROR: parser', err)
        return None
    except UnboundLocalError as err:
        print('ERROR: parsed string', err)
        return None
    except UnicodeDecodeError as err:
        print('ERROR: unicode', err)
        return None

    # first, try header
    pagedate = examine_header(tree)
    if pagedate is not None and date_validator(pagedate) is True:
        return pagedate

    # <time>
    elements = tree.xpath('//time')
    if elements is not None:
        for elem in elements:
            if 'datetime' in elem.attrib:
                attempt = try_date(elem.get('datetime'))
                if attempt is not None and date_validator(attempt) is True:
                    return attempt # break

    # expressions + text_content
    for expr in DATE_EXPRESSIONS:
        dateresult = examine_date_elements(tree, expr)
        if dateresult is not None and date_validator(dateresult) is True:
            return dateresult # break

    # date regex timestamp rescue
    match = re.search(r'([0-9]{4}-[0-9]{2}-[0-9]{2}).[0-9]{2}:[0-9]{2}:[0-9]{2}', htmlstring)
    if match and date_validator(match.group(1)) is True:
        pagedate = match.group(1)

    # last resort
    pagedate = search_page(htmlstring)

    return pagedate

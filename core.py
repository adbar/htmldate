#!/usr/bin/python3
# -*- coding: utf-8 -*-

## This code is available from https://github.com/adbar/htmldoc-dating
## under GNU GPL v3 license



# Noteworthy sources
# https://github.com/ianstormtaylor/metascraper/blob/master/lib/rules/date.js
# https://github.com/grangier/python-goose/blob/develop/goose/extractors/publishdate.py
# https://github.com/codelucas/newspaper/blob/master/newspaper/extractors.py




from __future__ import print_function, unicode_literals


# standard
import datetime
import re
import time

from collections import defaultdict
from io import StringIO # python3

# third-party
import dateparser

from lxml import etree, html

# own
# import settings





DATE_EXPRESSIONS = ["//*[starts-with(@id, 'date')]", "//*[starts-with(@class, 'date')]", "//*[starts-with(@class, 'byline')]", "//*[starts-with(@class, 'entry-date')]", "//*[starts-with(@class, 'post-meta')]", "//*[starts-with(@class, 'postmetadata')]"]

OUTPUTFORMAT = '%Y-%m-%d'



def try_date(string):
    target = dateparser.parse(string, settings={'PREFER_DAY_OF_MONTH': 'first', 'PREFER_DATES_FROM': 'past', 'DATE_ORDER': 'DMY'})
    if target is not None:
        # test year for conformity
        year = int(datetime.date.strftime(target, '%Y'))
        if 1995 < year < 2020:
            return datetime.date.strftime(target, OUTPUTFORMAT)
    return None



def examine_date_elements(tree, expression):
    elements = tree.xpath(expression)
    if elements is not None:
        for elem in elements:
            # simple length heuristics
            if 3 < len(elem.text_content().strip()) < 30:
                print('# DEBUG analyzing:', html.tostring(elem, pretty_print=False, encoding='unicode'), elem.text_content().strip())
                attempt = try_date(elem.text_content().strip())
                if attempt is not None:
                    print('# DEBUG result:', attempt)
                    return attempt
    return None



def examine_header(tree):
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

    return headerdate





def search_page(htmlstring):
    # init
    pagedate = None

    # date ultimate rescue for the rest: most frequent year/month comination in the HTML
    ## this is risky
    ## TODO: refactor

    # 1
    dic = defaultdict(int)
    try:
        for expression in re.findall(r'/([0-9]{4}/[0-9]{2})/', htmlstring):
            dic[expression] += 1
        vals = list(dic.values())
        k = list(dic.keys())
        try:
            match = re.match(r'([0-9]{4})/([0-9]{2})', k[vals.index(max(vals))])
            if match:
                pagedate = '-'.join([match.group(1), match.group(2), '01'])
                return pagedate
        except ValueError:
            pass
    except UnboundLocalError:
        pass

    # 2
    dic = defaultdict(int)
    try:
        for expression in re.findall(r'\D([0-9]{2}[/.][0-9]{4})\D', htmlstring):
            dic[expression] += 1
        vals = list(dic.values())
        k = list(dic.keys())
        try:
            match = re.match(r'([0-9]{2})[/.]([0-9]{4})', k[vals.index(max(vals))])
            if match:
                pagedate = '-'.join([match.group(2), match.group(1), '01'])
                return pagedate
        except ValueError:
            pass
    except UnboundLocalError:
        pass

    # last try
    dic = defaultdict(int)
    try:
        for expression in re.findall(r'\D(2[01][0-9]{2})\D', htmlstring):
            dic[expression] += 1
        vals = list(dic.values())
        k = list(dic.keys())
        if 1995 < int(k[vals.index(max(vals))]) < 2020:
            pagedate = '-'.join([k[vals.index(max(vals))], '07', '01'])
        else:
            for expression in re.findall(r'\D(2[01][0-9]{2})\D', htmlstring):
                if 1995 < int(expression) < 2020:
                    pagedate = '-'.join([expression, '07', '01'])
                    return pagedate
    except (UnboundLocalError, ValueError):
        pass

    return None



def find_date(htmlstring):
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

    # first, try header
    pagedate = examine_header(tree)
    if pagedate is not None:
        return pagedate

    # <time>
    elements = tree.xpath('//time')
    if elements is not None:
        for elem in elements:
            if 'datetime' in elem.attrib:
                attempt = try_date(elem.get('datetime'))
                if attempt is not None:
                    pagedate = attempt
                    return pagedate # break

    # expressions + text_content
    for expr in DATE_EXPRESSIONS:
        dateresult = examine_date_elements(tree, expr)
        if dateresult is not None:
            pagedate = dateresult
            return pagedate # break

    # date regex timestamp rescue
    match = re.search(r'([0-9]{4}-[0-9]{2}-[0-9]{2}).[0-9]{2}:[0-9]{2}:[0-9]{2}', htmlstring)
    if match:
        pagedate = match.group(1)

    # last resort
    pagedate = search_page(htmlstring)

    return pagedate

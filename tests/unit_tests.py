# -*- coding: utf-8 -*-
"""
Unit tests for the htmldate library.
"""

import os
# import unittest
# https://docs.pytest.org/en/latest/

import htmldate


MOCK_PAGES = { \
                'http://blog.python.org/2016/12/python-360-is-now-available.html': 'samples/blog.python.org.html', \
                'https://example.com': 'samples/example.com.html', \
                'https://github.com/adbar/htmldate': 'samples/github.com.html', \
}

TEST_DIR = os.path.abspath(os.path.dirname(__file__))



def load_mock_page(url):
    '''load mock page from samples'''
    with open(os.path.join(TEST_DIR, MOCK_PAGES[url]), 'r') as inputf:
        htmlstring = inputf.read()
    return htmlstring


def test_no_date():
    '''this page should return no date'''
    assert htmldate.find_date(load_mock_page('https://example.com')) == None


def test_exact_date():
    '''this page should return an exact date'''
    assert htmldate.find_date(load_mock_page('http://blog.python.org/2016/12/python-360-is-now-available.html')) == '2016-12-23'


def test_approximate_date():
    '''this page should return an approximate date'''
    assert htmldate.find_date(load_mock_page('https://github.com/adbar/htmldate')) == '2016-12-01'


def test_date_validator():
    '''test internal date validation'''
    assert htmldate.date_validator('2016-01-01') == True
    assert htmldate.date_validator('1998-08-08') == True
    assert htmldate.date_validator('1992-07-30') == False
    assert htmldate.date_validator('1901-13-98') == False
    assert htmldate.date_validator('202-01') == False


def test_search_pattern():
    '''test pattern search in strings'''
    # pattern 1
    assert htmldate.search_pattern('http://www.url.net/index.html', '/([0-9]{4}/[0-9]{2})/') is None
    assert htmldate.search_pattern('http://www.url.net/2016/01/index.html', '/([0-9]{4}/[0-9]{2})/') is not None
    # pattern 2
    assert htmldate.search_pattern('It happened on the 202.E.19, the day when it all began.', '\D([0-9]{2}[/.][0-9]{4})\D') is None
    assert htmldate.search_pattern('It happened on the 15.02.2002, the day when it all began.', '\D([0-9]{2}[/.][0-9]{4})\D') is not None
    # pattern 3
    assert htmldate.search_pattern('It happened in the film 300.', '\D(2[01][0-9]{2})\D') is None
    assert htmldate.search_pattern('It happened in 2002.', '\D(2[01][0-9]{2})\D') is not None




if __name__ == '__main__':
    # function-level
    test_date_validator()
    test_search_pattern()

    # module-level
    test_no_date()
    test_exact_date()
    test_approximate_date()

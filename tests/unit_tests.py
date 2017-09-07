# -*- coding: utf-8 -*-
"""
Unit tests for the htmldate library.
"""

import os
# import unittest
# https://docs.pytest.org/en/latest/

import htmldate


MOCK_PAGES = { \
                'http://blog.python.org/2016/12/python-360-is-now-available.html': 'cache/blog.python.org.html', \
                'https://example.com': 'cache/example.com.html', \
                'https://github.com/adbar/htmldate': 'cache/github.com.html', \
                'https://creativecommons.org/about/': 'cache/creativecommons.org.html', \
                'https://en.support.wordpress.com/': 'cache/support.wordpress.com.html', \
                'https://en.blog.wordpress.com/': 'cache/blog.wordpress.com.html', \
                'https://www.deutschland.de/en': 'cache/deutschland.de.en.html', \
                'https://www.gnu.org/licenses/gpl-3.0.en.html': 'cache/gnu.org.gpl.html', \
                'https://opensource.org/': 'cache/opensource.org.html', \
                'https://www.austria.info/': 'cache/austria.info.html', \
}

TEST_DIR = os.path.abspath(os.path.dirname(__file__))



def load_mock_page(url):
    '''load mock page from samples'''
    with open(os.path.join(TEST_DIR, MOCK_PAGES[url]), 'r') as inputf:
        htmlstring = inputf.read()
    return htmlstring


def test_no_date():
    '''this page should not return any date'''
    assert htmldate.find_date(load_mock_page('https://example.com')) is None
    assert htmldate.find_date(load_mock_page('https://en.support.wordpress.com/')) is None


def test_exact_date():
    '''these pages should return an exact date'''
    # meta in header
    assert htmldate.find_date(load_mock_page('http://blog.python.org/2016/12/python-360-is-now-available.html')) == '2016-12-23'
    # in document body
    assert htmldate.find_date(load_mock_page('https://github.com/adbar/htmldate')) == '2017-08-25'
    assert htmldate.find_date(load_mock_page('https://en.blog.wordpress.com/')) == '2017-08-30'
    assert htmldate.find_date(load_mock_page('https://www.gnu.org/licenses/gpl-3.0.en.html')) == '2016-11-18'
    # test assert htmldate.find_date(load_mock_page('https://opensource.org/')) == '2017-09-05'
    assert htmldate.find_date(load_mock_page('https://www.austria.info/')) == '2017-09-07'


def test_approximate_date():
    '''this page should return an approximate date'''
    assert htmldate.find_date(load_mock_page('https://creativecommons.org/about/')) == '2017-08-11' # or '2017-08-03'
    assert htmldate.find_date(load_mock_page('https://www.deutschland.de/en')) == '2017-08-01' # or?


def test_date_validator():
    '''test internal date validation'''
    assert htmldate.date_validator('2016-01-01') is True
    assert htmldate.date_validator('1998-08-08') is True
    assert htmldate.date_validator('1992-07-30') is False
    assert htmldate.date_validator('1901-13-98') is False
    assert htmldate.date_validator('202-01') is False


def test_try_date():
    '''test date extraction via external package'''
    assert htmldate.try_date('Friday, September 01, 2017') == '2017-09-01'
    assert htmldate.try_date('Fr, 1 Sep 2017 16:27:51 MESZ') == '2017-09-01'
    assert htmldate.try_date('Freitag, 01. September 2017') == '2017-09-01'
    # assert htmldate.try_date('Am 1. September 2017 um 15:36 Uhr schrieb') == '2017-09-01'
    assert htmldate.try_date('1.9.2017') == '2017-09-01'
    assert htmldate.try_date('1/9/2017') == '2017-09-01'
    assert htmldate.try_date('201709011234') == '2017-09-01'


def test_search_pattern():
    '''test pattern search in strings'''
    # pattern 1
    pattern = '\D([0-9]{4}[/.-][0-9]{2})\D'
    catch = '([0-9]{4})[/.-]([0-9]{2})'
    yearpat = '^([12][0-9]{3})'
    assert htmldate.search_pattern('It happened on the 202.E.19, the day when it all began.', pattern, catch, yearpat) is None
    assert htmldate.search_pattern('The date is 2002.02.15.', pattern, catch, yearpat) is not None
    assert htmldate.search_pattern('http://www.url.net/index.html', pattern, catch, yearpat) is None
    assert htmldate.search_pattern('http://www.url.net/2016/01/index.html', pattern, catch, yearpat) is not None

    # pattern 2
    pattern = '\D([0-9]{2}[/.-][0-9]{4})\D'
    catch = '([0-9]{2})[/.-]([0-9]{4})'
    yearpat = '([12][0-9]{3})$'
    assert htmldate.search_pattern('It happened on the 202.E.19, the day when it all began.', pattern, catch, yearpat) is None
    assert htmldate.search_pattern('It happened on the 15.02.2002, the day when it all began.', pattern, catch, yearpat) is not None

    # pattern 3
    pattern = '\D(2[01][0-9]{2})\D'
    catch = '(2[01][0-9]{2})'
    yearpat = '^(2[01][0-9]{2})'
    assert htmldate.search_pattern('It happened in the film 300.', pattern, catch, yearpat) is None
    assert htmldate.search_pattern('It happened in 2002.', pattern, catch, yearpat) is not None


def test_cli():
    '''test the command-line interface'''
    pass


if __name__ == '__main__':
    # function-level
    test_date_validator()
    test_search_pattern()
    test_try_date()

    # module-level
    test_no_date()
    test_exact_date()
    test_approximate_date()

    # cli
    # test_cli() ## TODO

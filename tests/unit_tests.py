# -*- coding: utf-8 -*-
"""
Unit tests for the htmldate library.
"""

import logging
import os
import sys
# https://docs.pytest.org/en/latest/

import htmldate

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


MOCK_PAGES = { \
'http://blog.python.org/2016/12/python-360-is-now-available.html': 'blog.python.org.html', \
'https://example.com': 'example.com.html', \
'https://github.com/adbar/htmldate': 'github.com.html', \
'https://creativecommons.org/about/': 'creativecommons.org.html', \
'https://en.support.wordpress.com/': 'support.wordpress.com.html', \
'https://en.blog.wordpress.com/': 'blog.wordpress.com.html', \
'https://www.deutschland.de/en': 'deutschland.de.en.html', \
'https://www.gnu.org/licenses/gpl-3.0.en.html': 'gnu.org.gpl.html', \
'https://opensource.org/': 'opensource.org.html', \
'https://www.austria.info/': 'austria.info.html', \
'https://www.portal.uni-koeln.de/9015.html?&L=1&tx_news_pi1%5Bnews%5D=4621&tx_news_pi1%5Bcontroller%5D=News&tx_news_pi1%5Baction%5D=detail&cHash=7bc78dfe3712855026fc717c2ea8e0d3': 'uni-koeln.de.ocean.html', \
'https://www.intel.com/content/www/us/en/legal/terms-of-use.html': 'intel.com.tos.html', \
'http://www.greenpeace.org/international/en/campaigns/forests/asia-pacific/': 'greenpeace.org.forests.html', \
  'https://www.amnesty.org/en/what-we-do/corporate-accountability/': 'amnesty.org.corporate.html', \
'http://www.medef.com/en/content/alternative-dispute-resolution-for-antitrust-damages': 'medef.fr.dispute.html', \
'https://www.rosneft.com/business/Upstream/Licensing/': 'rosneft.com.licensing.html', \
'https://www.creativecommons.at/faircoin-hackathon': 'creativecommons.at.faircoin.html', \
'https://pixabay.com/en/service/terms/': 'pixabay.com.tos.html', \
'https://futurezone.at/digital-life/wie-creativecommons-richtig-genutzt-wird/24.600.504': 'futurezone.at.cc.html', \
'https://500px.com/photo/26034451/spring-in-china-by-alexey-kruglov': '500px.com.spring.html', \
'https://www.eff.org/files/annual-report/2015/index.html': 'eff.org.2015.html', \
'http://unexpecteduser.blogspot.de/2011/': 'unexpecteduser.2011.html', \
# '': '', \
}

TEST_DIR = os.path.abspath(os.path.dirname(__file__))



def load_mock_page(url):
    '''load mock page from samples'''
    with open(os.path.join(TEST_DIR, 'cache', MOCK_PAGES[url]), 'r') as inputf:
        htmlstring = inputf.read()
    return htmlstring


def test_no_date():
    '''this page should not return any date'''
    assert htmldate.find_date(load_mock_page('https://example.com')) is None
    assert htmldate.find_date(load_mock_page('https://www.intel.com/content/www/us/en/legal/terms-of-use.html')) is None
    # safe search
    assert htmldate.find_date(load_mock_page('https://en.support.wordpress.com/'), False) is None


def test_exact_date():
    '''these pages should return an exact date'''
    # meta in header
    assert htmldate.find_date(load_mock_page('http://blog.python.org/2016/12/python-360-is-now-available.html')) == '2016-12-23'
    assert htmldate.find_date(load_mock_page('https://500px.com/photo/26034451/spring-in-china-by-alexey-kruglov')) == '2013-02-16'
    # meta in document body
    assert htmldate.find_date(load_mock_page('https://futurezone.at/digital-life/wie-creativecommons-richtig-genutzt-wird/24.600.504')) == '2013-08-09'
    # in document body
    assert htmldate.find_date(load_mock_page('https://github.com/adbar/htmldate')) == '2017-08-25'
    assert htmldate.find_date(load_mock_page('https://en.blog.wordpress.com/')) == '2017-08-30'
    assert htmldate.find_date(load_mock_page('https://www.gnu.org/licenses/gpl-3.0.en.html')) == '2016-11-18'
    assert htmldate.find_date(load_mock_page('https://opensource.org/')) == '2017-09-05'
    assert htmldate.find_date(load_mock_page('https://www.austria.info/')) == '2017-09-07'
    assert htmldate.find_date(load_mock_page('https://www.portal.uni-koeln.de/9015.html?&L=1&tx_news_pi1%5Bnews%5D=4621&tx_news_pi1%5Bcontroller%5D=News&tx_news_pi1%5Baction%5D=detail&cHash=7bc78dfe3712855026fc717c2ea8e0d3')) == '2017-07-12'
    assert htmldate.find_date(load_mock_page('https://www.eff.org/files/annual-report/2015/index.html')) == '2016-05-04'
    assert htmldate.find_date(load_mock_page('http://unexpecteduser.blogspot.de/2011/')) == '2011-03-30'
    assert htmldate.find_date(load_mock_page('https://www.rosneft.com/business/Upstream/Licensing/')) == '2017-02-27' # most probably 2014-12-31, found in text


def test_approximate_date():
    '''this page should return an approximate date'''
    assert htmldate.find_date(load_mock_page('https://creativecommons.org/about/')) == '2017-08-11' # or '2017-08-03'
    assert htmldate.find_date(load_mock_page('https://www.deutschland.de/en')) == '2017-08-01' # or?
    assert htmldate.find_date(load_mock_page('http://www.greenpeace.org/international/en/campaigns/forests/asia-pacific/')) == '2017-07-01' # actually "28 April, 2017"
    assert htmldate.find_date(load_mock_page('https://www.amnesty.org/en/what-we-do/corporate-accountability/')) == '2017-07-01'
    assert htmldate.find_date(load_mock_page('http://www.medef.com/en/content/alternative-dispute-resolution-for-antitrust-damages')) == '2017-07-01' # actually 2017-09-01
    assert htmldate.find_date(load_mock_page('https://www.creativecommons.at/faircoin-hackathon')) == '2016-12-15' # actually 2017-07-24
    assert htmldate.find_date(load_mock_page('https://pixabay.com/en/service/terms/')) == '2017-07-01' # actually 2017-08-09


def test_date_validator():
    '''test internal date validation'''
    assert htmldate.date_validator('2016-01-01') is True
    assert htmldate.date_validator('1998-08-08') is True
    assert htmldate.date_validator('2001-12-31') is True
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


def test_search_html():
    '''test pattern search in HTML'''
    assert htmldate.search_page(load_mock_page('https://www.portal.uni-koeln.de/9015.html?&L=1&tx_news_pi1%5Bnews%5D=4621&tx_news_pi1%5Bcontroller%5D=News&tx_news_pi1%5Baction%5D=detail&cHash=7bc78dfe3712855026fc717c2ea8e0d3')) == '2017-07-12'


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
    test_search_html()

    # cli
    # test_cli() ## TODO

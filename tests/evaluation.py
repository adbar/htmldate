"""
Bundles extraction and evaluation functions for all libraries in the benchmark.
"""

import json
import os
import re

try:
    from cchardet import detect
except ImportError:
    from charset_normalizer import detect

from articleDateExtractor import extractArticlePublishedDate
from date_guesser import guess_date
from goose3 import Goose
from newspaper import Article
from newspaper.article import ArticleDownloadState
from newsplease import NewsPlease

from htmldate import find_date
from htmldate.validators import convert_date


TEST_DIR = os.path.abspath(os.path.dirname(__file__))
# list the jsons containing the pages here
eval_paths = ["eval_mediacloud_2020.json", "eval_default.json"]
# load the pages here
EVAL_PAGES = {}
for each in eval_paths:
    evalpath = os.path.join(TEST_DIR, each)
    with open(evalpath, "r", encoding="utf-8") as f:
        EVAL_PAGES.update(json.load(f))

G = Goose()


def load_document(filename):
    """load mock page from samples"""
    htmlstring = ""
    # look for the right directory
    for directory in ("test_set", "cache", "eval"):
        mypath = os.path.join(TEST_DIR, directory, filename)
        if os.path.isfile(mypath):
            break
    # open and convert the file to str
    try:
        with open(mypath, "r", encoding="utf-8") as inputf:
            htmlstring = inputf.read()
    # encoding/windows fix for the tests
    except UnicodeDecodeError:
        # read as binary
        with open(mypath, "rb") as inputf:
            htmlbinary = inputf.read()
        guessed_encoding = detect(htmlbinary)["encoding"]
        if guessed_encoding:
            try:
                htmlstring = htmlbinary.decode(guessed_encoding)
            except UnicodeDecodeError:
                pass
        if not htmlstring:
            # print("Encoding error, using binary:", mypath)
            htmlstring = htmlbinary
    return htmlstring


def run_htmldate_extensive(htmlstring):
    """run htmldate on content"""
    return find_date(htmlstring, original_date=True, extensive_search=True)


def run_htmldate_fast(htmlstring):
    """run htmldate on content"""
    return find_date(htmlstring, original_date=True, extensive_search=False)


def run_newspaper(htmlstring):
    """try with the newspaper module"""
    # throws error on the eval_default dataset
    try:
        myarticle = Article(htmlstring)
        myarticle.html = htmlstring
        myarticle.download_state = ArticleDownloadState.SUCCESS
        myarticle.parse()
    except (UnicodeDecodeError, UnicodeEncodeError):
        return None
    if myarticle.publish_date is None or myarticle.publish_date == "":
        return None
    return str(myarticle.publish_date)[0:10]


def run_newsplease(htmlstring):
    """try with newsplease"""
    try:
        article = NewsPlease.from_html(htmlstring, url=None)
        if article.date_publish is None:
            return None
        return convert_date(article.date_publish, "%Y-%m-%d %H:%M:%S", "%Y-%m-%d")
    except Exception as err:
        print("Exception:", err)
        return None


def run_articledateextractor(htmlstring):
    """try with articleDateExtractor"""
    dateresult = extractArticlePublishedDate("", html=htmlstring)
    if dateresult is None:
        return None
    return convert_date(dateresult, "%Y-%m-%d %H:%M:%S", "%Y-%m-%d")


def run_dateguesser(htmlstring):
    """try with date_guesser"""
    guess = guess_date(url="https://www.example.org/test/", html=htmlstring)
    if guess.date is None:
        return None
    return convert_date(guess.date, "%Y-%m-%d %H:%M:%S", "%Y-%m-%d")


def run_goose(htmlstring):
    """try with the goose algorithm"""
    try:
        article = G.extract(raw_html=htmlstring)
    except (AttributeError, UnicodeDecodeError):
        return None
    if article.publish_date is None:
        return None
    try:
        datematch = re.match(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", article.publish_date)
        return datematch[0]
    # illogical result
    except TypeError:
        #    print(article.publish_date)
        return None


def evaluate_result(result, data):
    """evaluate result contents"""
    # template: tp, fp, tn, fn
    datereference = data["date"]
    if result is None:
        return (0, 0, 1, 1) if datereference is None else (0, 0, 0, 1)
    return (1, 0, 0, 0) if result == datereference else (0, 1, 0, 0)

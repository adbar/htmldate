"""
Compare extraction results with other libraries of the same kind.
"""

# import logging
import os
import re
import time
import json

from lxml import etree, html

try:
    from cchardet import detect
except ImportError:
    from charset_normalizer import detect

from articleDateExtractor import extractArticlePublishedDate
from date_guesser import guess_date, Accuracy
from goose3 import Goose
from htmldate import find_date
from htmldate.validators import convert_date
from newspaper import Article
from newspaper.article import ArticleDownloadState
from newsplease import NewsPlease
from tabulate import tabulate



# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
#list the jsons containing the pages here
eval_paths = ['eval_mediacloud_2020.json', 'eval_default.json']
#load the pages here
EVAL_PAGES = {}
for each in eval_paths:
    evalpath = os.path.join(TEST_DIR, each)
    with open(evalpath) as f:
        EVAL_PAGES.update(json.load(f))


def load_document(filename):
    '''load mock page from samples'''
    mypath = os.path.join(TEST_DIR, 'test_set', filename)
    if not os.path.isfile(mypath):
        mypath = os.path.join(TEST_DIR, 'cache', filename)
        if not os.path.isfile(mypath):
            mypath = os.path.join(TEST_DIR, 'eval', filename)
    try:
        with open(mypath, 'r') as inputf:
            htmlstring = inputf.read()
    # encoding/windows fix for the tests
    except UnicodeDecodeError:
        # read as binary
        with open(mypath, 'rb') as inputf:
            htmlbinary = inputf.read()
        guessed_encoding = detect(htmlbinary)['encoding']
        if guessed_encoding is not None:
            try:
                htmlstring = htmlbinary.decode(guessed_encoding)
            except UnicodeDecodeError:
                htmlstring = htmlbinary
        else:
            print('Encoding error')
    return htmlstring
# bypass not possible: error by newspaper
#    with open(mypath, 'rb') as inputf:
#        return inputf.read()


def run_htmldate_extensive(htmlstring):
    '''run htmldate on content'''
    return find_date(htmlstring, original_date=True, extensive_search=True)


def run_htmldate_fast(htmlstring):
    '''run htmldate on content'''
    return find_date(htmlstring, original_date=True, extensive_search=False)


def run_newspaper(htmlstring):
    '''try with the newspaper module'''
    # throws error on the eval_default dataset
    try:
        myarticle = Article(htmlstring)
    except (TypeError, UnicodeDecodeError):
        return None
    myarticle.html = htmlstring
    myarticle.download_state = ArticleDownloadState.SUCCESS
    myarticle.parse()
    if myarticle.publish_date is None or myarticle.publish_date == '':
        return None
    return convert_date(myarticle.publish_date, '%Y-%m-%d %H:%M:%S', '%Y-%m-%d')


def run_newsplease(htmlstring):
    '''try with newsplease'''
    try:
        article = NewsPlease.from_html(htmlstring, url=None)
        if article.date_publish is None:
             return None
        return convert_date(article.date_publish, '%Y-%m-%d %H:%M:%S', '%Y-%m-%d')
    except Exception as err:
        print('Exception:', err)
        return None


def run_articledateextractor(htmlstring):
    '''try with articleDateExtractor'''
    dateresult = extractArticlePublishedDate('', html=htmlstring)
    if dateresult is None:
       return None
    return convert_date(dateresult, '%Y-%m-%d %H:%M:%S', '%Y-%m-%d')


def run_dateguesser(htmlstring):
    '''try with date_guesser'''
    guess = guess_date(url='https://www.example.org/test/', html=htmlstring)
    if guess.date is None:
       return None
    return convert_date(guess.date, '%Y-%m-%d %H:%M:%S', '%Y-%m-%d')


def run_goose(htmlstring):
    '''try with the goose algorithm'''
    g = Goose()
    article = g.extract(raw_html=htmlstring)
    if article.publish_date is None:
        return None
    datematch = re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', article.publish_date)
    try:
        return datematch.group(0)
    # illogical result
    except AttributeError:
    #    print(article.publish_date)
        return None


def evaluate_result(result, EVAL_PAGES, item):
    '''evaluate result contents'''
    true_positives = 0
    false_positives = 0
    true_negatives = 0 # not in use (yet)
    false_negatives = 0
    datereference = EVAL_PAGES[item]['date']
    if result is None and datereference is None:
        true_negatives += 1
    elif result is None:
        false_negatives += 1
    elif result == datereference:
        true_positives += 1
    else:
        false_positives += 1
    return true_positives, false_positives, true_negatives, false_negatives


def calculate_scores(name, mydict):
    '''output weighted result score'''
    tp, fn, fp, tn = mydict['true_positives'], mydict['false_negatives'], mydict['false_positives'], mydict['true_negatives']
    time_num1 = mydict['time'] / htmldate_extensive_result['time']
    time1 = "{:.2f}x".format(time_num1)
    time_num2 = mydict['time'] / htmldate_fast_result['time']
    time2 = "{:.2f}x".format(time_num2)
    precision = tp/(tp+fp)
    recall = tp/(tp+fn)
    accuracy = (tp+tn)/(tp+tn+fp+fn)
    fscore = (2*tp)/(2*tp + fp + fn)  # 2*((precision*recall)/(precision+recall))
    return name, precision, recall, accuracy, fscore, mydict['time'], time1, time2,


template_dict = {'true_positives': 0, 'false_positives': 0, 'true_negatives': 0, 'false_negatives': 0, 'time': 0}
everything, nothing, htmldate_extensive_result, htmldate_fast_result, newspaper_result, newsplease_result, articledateextractor_result, dateguesser_result, goose_result = {}, {}, {}, {}, {}, {}, {}, {}, {}
everything.update(template_dict)
nothing.update(template_dict)
htmldate_extensive_result.update(template_dict)
htmldate_fast_result.update(template_dict)
newspaper_result.update(template_dict)
newsplease_result.update(template_dict)
articledateextractor_result.update(template_dict)
dateguesser_result.update(template_dict)
goose_result.update(template_dict)


i = 0

for item in EVAL_PAGES:
    i += 1
    #print(item)
    htmlstring = load_document(EVAL_PAGES[item]['file'])
    # null hypotheses
    tp, fp, tn, fn = evaluate_result(None, EVAL_PAGES, item)
    nothing['true_positives'] += tp
    nothing['false_positives'] += fp
    nothing['true_negatives'] += tn
    nothing['false_negatives'] += fn
    # htmldate
    start = time.time()
    result = run_htmldate_extensive(htmlstring)
    htmldate_extensive_result['time'] += time.time() - start
    tp, fp, tn, fn = evaluate_result(result, EVAL_PAGES, item)
    htmldate_extensive_result['true_positives'] += tp
    htmldate_extensive_result['false_positives'] += fp
    htmldate_extensive_result['true_negatives'] += tn
    htmldate_extensive_result['false_negatives'] += fn
    # htmldate fast
    start = time.time()
    result = run_htmldate_fast(htmlstring)
    htmldate_fast_result['time'] += time.time() - start
    tp, fp, tn, fn = evaluate_result(result, EVAL_PAGES, item)
    htmldate_fast_result['true_positives'] += tp
    htmldate_fast_result['false_positives'] += fp
    htmldate_fast_result['true_negatives'] += tn
    htmldate_fast_result['false_negatives'] += fn
    # newspaper
    start = time.time()
    result = run_newspaper(htmlstring)
    newspaper_result['time'] += time.time() - start
    tp, fp, tn, fn = evaluate_result(result, EVAL_PAGES, item)
    newspaper_result['true_positives'] += tp
    newspaper_result['false_positives'] += fp
    newspaper_result['true_negatives'] += tn
    newspaper_result['false_negatives'] += fn
    # newsplease
    start = time.time()
    result = run_newsplease(htmlstring)
    newsplease_result['time'] += time.time() - start
    tp, fp, tn, fn = evaluate_result(result, EVAL_PAGES, item)
    newsplease_result['true_positives'] += tp
    newsplease_result['false_positives'] += fp
    newsplease_result['true_negatives'] += tn
    newsplease_result['false_negatives'] += fn
    # articledateextractor
    start = time.time()
    result = run_articledateextractor(htmlstring)
    articledateextractor_result['time'] += time.time() - start
    tp, fp, tn, fn = evaluate_result(result, EVAL_PAGES, item)
    articledateextractor_result['true_positives'] += tp
    articledateextractor_result['false_positives'] += fp
    articledateextractor_result['true_negatives'] += tn
    articledateextractor_result['false_negatives'] += fn
    # date_guesser
    start = time.time()
    result = run_dateguesser(htmlstring)
    dateguesser_result['time'] += time.time() - start
    tp, fp, tn, fn = evaluate_result(result, EVAL_PAGES, item)
    dateguesser_result['true_positives'] += tp
    dateguesser_result['false_positives'] += fp
    dateguesser_result['true_negatives'] += tn
    dateguesser_result['false_negatives'] += fn
    # goose
    start = time.time()
    result = run_goose(htmlstring)
    goose_result['time'] += time.time() - start
    tp, fp, tn, fn = evaluate_result(result, EVAL_PAGES, item)
    goose_result['true_positives'] += tp
    goose_result['false_positives'] += fp
    goose_result['true_negatives'] += tn
    goose_result['false_negatives'] += fn


print('Sample Size:', i)
table = [calculate_scores("htmldate extensive", htmldate_extensive_result), calculate_scores("htmldate fast", htmldate_fast_result),
calculate_scores("newspaper", newspaper_result),
calculate_scores("newsplease", newsplease_result), calculate_scores("articledateextractor", articledateextractor_result),
calculate_scores("date_guesser", dateguesser_result),  calculate_scores("goose", goose_result)
]
print(tabulate(table, headers = ["Name", "Precision", "Recall", "Accuracy", "F-score", "Time (s)", "Time (Relative to htmldate extensive)", "Time (Relative to htmldate fast)"], floatfmt=[".3f", ".3f", ".3f", ".3f", ".3f", ".3f"]))


with open('comparison_results.txt', 'w') as f:
    print(tabulate(table, headers = ["Name", "Precision", "Recall", "Accuracy", "F-score", "Time (s)", "Time (Relative to htmldate extensive)", "Time (Relative to htmldate fast)"], floatfmt=[".3f", ".3f", ".3f", ".3f", ".3f", ".3f"]), file=f)
print("Results also saved as comparison_results.txt")

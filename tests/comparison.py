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
    import cchardet as chardet
except ImportError:
    import chardet

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

#load the pages here
with open("eval_mediacloud_2020.json") as f:
    EVAL_PAGES = json.load(f)


def load_document(filename):
    '''load mock page from samples'''
    mypath = os.path.join(TEST_DIR, 'test_set', filename)
    try:
        with open(mypath, 'r') as inputf:
            htmlstring = inputf.read()
    # encoding/windows fix for the tests
    except UnicodeDecodeError:
        # read as binary
        with open(mypath, 'rb') as inputf:
            htmlbinary = inputf.read()
        guessed_encoding = chardet.detect(htmlbinary)['encoding']
        if guessed_encoding is not None:
            try:
                htmlstring = htmlbinary.decode(guessed_encoding)
            except UnicodeDecodeError:
                htmlstring = htmlbinary
        else:
            print('Encoding error')
    return htmlstring


def run_htmldate_extensive(htmlstring):
    '''run htmldate on content'''
    result = find_date(htmlstring, original_date=True, extensive_search=True)
    return result


def run_htmldate_fast(htmlstring):
    '''run htmldate on content'''
    result = find_date(htmlstring, original_date=True, extensive_search=False)
    return result


#def run_newspaper(htmlstring):
#    '''try with the newspaper module'''
#    ## does not work!
#    myarticle = Article('https://www.example.org/test/')
#    myarticle.html = htmlstring
#    myarticle.download_state = ArticleDownloadState.SUCCESS
#    myarticle.parse()
#    if myarticle.publish_date is None:
#        return None
#    date = convert_date(myarticle.publish_date, '%Y-%m-%d %H:%M:%S', '%Y-%m-%d')
#    return date


def run_newsplease(htmlstring):
    '''try with newsplease'''
    try:
        article = NewsPlease.from_html(htmlstring, url=None)
        if article.date_publish is None:
             return None
        date = convert_date(article.date_publish, '%Y-%m-%d %H:%M:%S', '%Y-%m-%d')
        return date
    except Exception as err:
        print('Exception:', err)
        return None


def run_articledateextractor(htmlstring):
   '''try with articleDateExtractor'''
   dateresult = extractArticlePublishedDate('', html=htmlstring)
   if dateresult is None:
      return None
   date = convert_date(dateresult, '%Y-%m-%d %H:%M:%S', '%Y-%m-%d')
   return date


def run_dateguesser(htmlstring):
   '''try with date_guesser'''
   guess = guess_date(url='https://www.example.org/test/', html=htmlstring)
   if guess.date is None:
      return None
   date = convert_date(guess.date, '%Y-%m-%d %H:%M:%S', '%Y-%m-%d')
   return date


def run_goose(htmlstring):
    '''try with the goose algorithm'''
    g = Goose()
    article = g.extract(raw_html=htmlstring)
    if article.publish_date is None:
        return None
    datematch = re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', article.publish_date)
    try:
        result = datematch.group(0)
        return result
    # illogical result
    except AttributeError:
        print(article.publish_date)
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
    elif result is None and datereference is not None:
        false_negatives += 1
    elif result == datereference:
        true_positives += 1
    else:
        false_positives += 1
    return true_positives, false_positives, true_negatives, false_negatives


def calculate_scores(name, mydict):
    '''output weighted result score'''
    tp, fn, fp, tn = mydict['true_positives'], mydict['false_negatives'], mydict['false_positives'], mydict['true_negatives']
    precision = tp/(tp+fp)
    recall = tp/(tp+fn)
    accuracy = (tp+tn)/(tp+tn+fp+fn)
    fscore = (2*tp)/(2*tp + fp + fn)  # 2*((precision*recall)/(precision+recall))
    return name, precision, recall, accuracy, fscore


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
    print(item)
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
   # result = run_newspaper(htmlstring)
   # newspaper_result['time'] += time.time() - start
   # tp, fp, tn, fn = evaluate_result(result, EVAL_PAGES, item)
   # newspaper_result['true_positives'] += tp
   # newspaper_result['false_positives'] += fp
   # newspaper_result['true_negatives'] += tn
   # newspaper_result['false_negatives'] += fn
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


#print('number of documents:', i)
#print('nothing (null hypothesis)')
#print(nothing)
## print(calculate_f_score(nothing))
#print('htmldate extensive')
#print(htmldate_extensive_result)
#print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(htmldate_extensive_result)))
#print("time diff.: %.2f" % (htmldate_extensive_result['time'] / htmldate_fast_result['time']))
#print('htmldate fast')
#print(htmldate_fast_result)
#print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(htmldate_fast_result)))
#print("time diff.: %.2f" % (htmldate_fast_result['time'] / htmldate_fast_result['time']))
##print('newspaper')
##print(newspaper_result)
##print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(newspaper_result)))
##print("time diff.: %.2f" % (newspaper_result['time'] / htmldate_fast_result['time']))
#print('newsplease')
#print(newsplease_result)
#print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(newsplease_result)))
#print("time diff.: %.2f" % (newsplease_result['time'] / htmldate_fast_result['time']))
#print('articledateextractor')
#print(articledateextractor_result)
#print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(articledateextractor_result)))
#print("time diff.: %.2f" % (articledateextractor_result['time'] / htmldate_fast_result['time']))
#print('date_guesser')
#print(dateguesser_result)
#print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(dateguesser_result)))
#print("time diff.: %.2f" % (dateguesser_result['time'] / htmldate_fast_result['time']))
#print('goose')
#print(goose_result)
#print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(goose_result)))
#print("time diff.: %.2f" % (goose_result['time'] / htmldate_fast_result['time']))

print('Sample Size:', i)
table = [calculate_scores("htmldate extensive", htmldate_extensive_result), calculate_scores("htmldate fast", htmldate_fast_result), 
calculate_scores("newsplease", newsplease_result), calculate_scores("articledateextractor", articledateextractor_result),
calculate_scores("date_guesser", dateguesser_result),  calculate_scores("goose", goose_result)]
print(tabulate(table, headers = ["Name", "Precision", "Recall", "Accuracy", "F-score"]))


with open('comparison_results.txt', 'w') as f:
    print(tabulate(table, headers = ["Name", "Precision", "Recall", "Accuracy", "F-score"]), file=f)
print("Results also saved as comparison_results.txt")
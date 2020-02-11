"""
Compare extraction results with other libraries of the same kind.
"""

# import logging
import os
import re
import time

from lxml import etree, html

try:
    import cchardet as chardet
except ImportError:
    import chardet


from htmldate import find_date
from htmldate.validators import convert_date
from newspaper import Article
from newsplease import NewsPlease


# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

TEST_DIR = os.path.abspath(os.path.dirname(__file__))


EVAL_PAGES = {
'https://die-partei.net/sh/': {
    'file': 'die-partei.net.sh.html',
    'date': '2014-07-19',
},
'http://blog.kinra.de/?p=959/': {
    'file': 'kinra.de.html',
    'date': '2012-12-16',
},
'http://blog.python.org/2016/12/python-360-is-now-available.html': {
    'file': 'blog.python.org.html',
    'date': '2016-12-23',
},
'http://blog.todamax.net/2018/midp-emulator-kemulator-und-brick-challenge/': {
    'file': 'blog.todamax.net.html',
    'date': '2018-02-15',
},
'http://carta.info/der-neue-trend-muss-statt-wunschkoalition/': {
    'file': 'carta.info.html',
    'date': '2012-05-08',
},
'https://500px.com/photo/26034451/spring-in-china-by-alexey-kruglov': {
    'file': '500px.com.spring.html',
    'date': '2013-02-16',
},
'https://bayern.de/': {
    'file': 'bayern.de.html',
    'date': '2017-10-06',
},
'https://creativecommons.org/about/': {
    'file': 'creativecommons.org.html',
    'date': '2016-05-22',
},
'https://en.blog.wordpress.com/': {
    'file': 'blog.wordpress.com.html',
    'date': '2017-08-30',
},
#'https://en.support.wordpress.com/': {
#    'file': 'support.wordpress.com.html',
#    'date': None,
#},
'https://futurezone.at/digital-life/wie-creativecommons-richtig-genutzt-wird/24.600.504': {
    'file': 'futurezone.at.cc.html',
    'date': '2013-08-09',
},
'https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/': {
    'file': 'netzpolitik.org.abmahnungen.html',
    'date': '2016-06-23',
},
'https://pixabay.com/en/service/terms/': {
    'file': 'pixabay.com.tos.html',
    'date': '2017-08-09',
},
'https://www.austria.info/': {
    'file': 'austria.info.html',
    'date': '2017-09-07',
},
'https://www.befifty.de/home/2017/7/12/unter-uns-montauk': {
    'file': 'befifty.montauk.html',
    'date': '2017-07-12',
},
'https://www.beltz.de/fachmedien/paedagogik/didacta_2019_in_koeln_19_23_februar/beltz_veranstaltungen_didacta_2016/veranstaltung.html?tx_news_pi1%5Bnews%5D=14392&tx_news_pi1%5Bcontroller%5D=News&tx_news_pi1%5Baction%5D=detail&cHash=10b1a32fb5b2b05360bdac257b01c8fa': {
    'file': 'beltz.de.didakta.html',
    'date': '2019-02-20',
},
'https://www.channelpartner.de/a/sieben-berufe-die-zukunft-haben,3050673': {
    'file': 'channelpartner.de.berufe.html',
    'date': '2019-04-03',
},
'https://www.creativecommons.at/faircoin-hackathon': {
    'file': 'creativecommons.at.faircoin.html',
    'date': '2017-07-24',
},
'https://www.eff.org/files/annual-report/2015/index.html': {
    'file': 'eff.org.2015.html',
    'date': '2016-05-04',
},
'https://www.facebook.com/visitaustria/': {
    'file': 'facebook.com.visitaustria.html',
    'date': '2017-10-06',
},
'https://www.gnu.org/licenses/gpl-3.0.en.html': {
    'file': 'gnu.org.gpl.html',
    'date': '2016-11-18',
},
'https://www.goodform.ch/blog/schattiges_plaetzchen': {
    'file': 'goodform.ch.blog.html',
    'date': '2018-06-27',
},
'https://www.horizont.net/marketing/kommentare/influencer-marketing-was-sich-nach-dem-vreni-frost-urteil-aendert-und-aendern-muss-172529': {
    'file': 'horizont.net.html',
    'date': '2019-01-29',
},
#'https://www.intel.com/content/www/us/en/legal/terms-of-use.html': {
#    'file': 'intel.com.tos.html',
#    'date': None,
#},
#'https://www.pferde-fuer-unsere-kinder.de/unsere-projekte/': {
#    'file': 'pferde.projekte.de.html',
#    'date': '2016-07-15',
#},
#'https://www.rosneft.com/business/Upstream/Licensing/': {
#    'file': 'rosneft.com.licensing.html',
#    'date': '2014-12-31',
#},
'https://www.scs78.de/news/items/warm-war-es-schoen-war-es.html': {
    'file': 'scs78.de.html',
    'date': '2018-06-10',
},
'https://www.tagesausblick.de/Analyse/USA/DOW-Jones-Jahresendrally-ade__601.html': {
    'file': 'tagesausblick.de.dow.html',
    'date': '2012-12-22',
},
'https://www.transgen.de/aktuell/2687.afrikanische-schweinepest-genome-editing.html': {
    'file': 'transgen.de.aktuell.html',
    'date': '2018-01-18',
},
'https://www.weltwoche.ch/ausgaben/2019-4/artikel/forbes-die-weltwoche-ausgabe-4-2019.html': {
    'file': 'weltwoche.ch.html',
    'date': '2019-01-23',
},
'http://www.freundeskreis-videoclips.de/waehlen-sie-car-player-tipps-zur-auswahl-der-besten-car-cd-player/': {
    'file': 'freundeskreis-videoclips.de.html',
    'date': '2017-07-12',
},
'https://www.wunderweib.de/manuela-reimann-hochzeitsueberraschung-in-bayern-107930.html': {
    'file': 'wunderweib.html',
    'date': '2019-06-20',
},
'http://unexpecteduser.blogspot.de/2011/': {
    'file': 'unexpecteduser.2011.html',
    'date': '2011-03-30',
},
#'http://viehbacher.com/de/spezialisierung/internationale-forderungsbeitreibung': {
#    'file': 'viehbacher.com.forderungsbetreibung.html',
#    'date': '2016-01-01',
#},
'http://www.eza.gv.at/das-ministerium/presse/aussendungen/2018/07/aussenministerin-karin-kneissl-beim-treffen-der-deutschsprachigen-aussenminister-in-luxemburg/': {
    'file': 'eza.gv.at.html',
    'date': '2018-07-03',
},
'http://www.greenpeace.org/international/en/campaigns/forests/asia-pacific/': {
    'file': 'greenpeace.org.forests.html',
    'date': '2017-04-28',
},
#'http://www.heimicke.de/chronik/zahlen-und-daten/': {
#    'file': 'heimicke.de.zahlen.html',
#    'date': '',
#},
'http://www.hobby-werkstatt-blog.de/arduino/424-eine-arduino-virtual-wall-fuer-den-irobot-roomba.php': {
    'file': 'hobby-werkstatt-blog.de.roomba.html',
    'date': '2015-12-14',
},
#'http://www.hundeverein-kreisunna.de/termine.html': {
#    'file': 'hundeverein-kreisunna.de.html',
#    'date': '',
#},
#'http://www.hundeverein-querfurt.de/index.php?option=com_content&view=article&id=54&Itemid=50': {
#    'file': 'hundeverein-querfurt.de.html',
#    'date': '',
#},
'http://www.jovelstefan.de/2012/05/11/parken-in-paris/': {
    'file': 'jovelstefan.de.parken.html',
    'date': '2012-05-11',
},
'http://www.klimawandel-global.de/klimaschutz/energie-sparen/elektromobilitat-der-neue-trend/': {
    'file': 'klimawandel-global.de.html',
    'date': '2013-05-03',
},
#'': {
#    'file': '',
#    'date': '',
#},
}




def load_document(filename):
    '''load mock page from samples'''
    dirname = 'cache'
    try:
        with open(os.path.join(TEST_DIR, dirname, filename), 'r') as inputf:
            htmlstring = inputf.read()
    # encoding/windows fix for the tests
    except UnicodeDecodeError:
        # read as binary
        with open(os.path.join(TEST_DIR, dirname, filename), 'rb') as inputf:
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


def run_htmldate(htmlstring):
    '''run htmldate on content'''
    result = find_date(htmlstring, original_date=True)
    return result


def run_newspaper(htmlstring):
    '''try with the newspaper module'''
    ## does not work!
    article = Article(htmlstring)
    return article.publish_date


def run_newsplease(htmlstring):
   '''try with newsplease'''
   article = NewsPlease.from_html(htmlstring, url=None)
   if article.date_publish is None:
      return None
   date = convert_date(article.date_publish, '%Y-%m-%d %H:%M:%S', '%Y-%m-%d')
   return date



def evaluate_result(result, EVAL_PAGES, item):
    '''evaluate result contents'''
    positives = 0
    negatives = 0
    datereference = EVAL_PAGES[item]['date']
    if result == datereference:
        positives += 1
    else:
        negatives += 1
    return positives, negatives


def calculate_scores(mydict):
    '''output weighted result score'''
    pos, neg = mydict['positives'], mydict['negatives']
    accuracy = pos/(pos+neg)
    return accuracy


template_dict = {'positives': 0, 'negatives': 0, 'time': 0}
everything, nothing, htmldate_result, newspaper_result, newsplease_result = {}, {}, {}, {}, {}
everything.update(template_dict)
nothing.update(template_dict)
htmldate_result.update(template_dict)
newspaper_result.update(template_dict)
newsplease_result.update(template_dict)

i = 0

for item in EVAL_PAGES:
    i += 1
    print(item)
    htmlstring = load_document(EVAL_PAGES[item]['file'])
    # null hypotheses
    positives, negatives = evaluate_result('', EVAL_PAGES, item)
    nothing['positives'] += positives
    nothing['negatives'] += negatives
    # htmldate
    start = time.time()
    result = run_htmldate(htmlstring)
    htmldate_result['time'] += time.time() - start
    positives, negatives = evaluate_result(result, EVAL_PAGES, item)
    htmldate_result['positives'] += positives
    htmldate_result['negatives'] += negatives
    # newspaper
    #start = time.time()
    #result = run_newspaper(htmlstring)
    #newspaper_result['time'] += time.time() - start
    #positives, negatives = evaluate_result(result, EVAL_PAGES, item)
    #newspaper_result['positives'] += positives
    #newspaper_result['negatives'] += negatives
    # newsplease
    start = time.time()
    result = run_newsplease(htmlstring)
    newsplease_result['time'] += time.time() - start
    positives, negatives = evaluate_result(result, EVAL_PAGES, item)
    newsplease_result['positives'] += positives
    newsplease_result['negatives'] += negatives


print('number of documents:', i)
print('nothing')
print(nothing)
# print(calculate_f_score(nothing))
#print('everything')
#print(everything)
#print("precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f" % (calculate_scores(everything)))
print('htmldate')
print(htmldate_result)
print("accuracy: %.3f" % (calculate_scores(htmldate_result)))
#print('newspaper')
#print(newspaper_result)
#print("accuracy: %.3f" % (calculate_scores(newspaper_result)))
print('newsplease')
print(newsplease_result)
print("accuracy: %.3f" % (calculate_scores(newsplease_result)))

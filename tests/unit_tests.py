# pylint:disable-msg=W1401
"""
Unit tests for the htmldate library.
"""


import datetime
import io
import logging
import os
import re
import sys

import pytest

from collections import Counter
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

try:
    import dateparser
    EXT_PARSER = True
    PARSER = dateparser.DateDataParser(languages=['de', 'en'], settings={'PREFER_DAY_OF_MONTH': 'first', 'PREFER_DATES_FROM': 'past', 'DATE_ORDER': 'DMY'}) # allow_redetect_language=False,
except ImportError:
    EXT_PARSER = False

from lxml import html

from htmldate.cli import examine, main, parse_args, process_args
from htmldate.core import compare_reference, examine_date_elements, find_date, search_page, search_pattern, select_candidate, try_ymd_date
from htmldate.extractors import custom_parse, external_date_parser, extract_partial_url_date, regex_parse
from htmldate.settings import MIN_DATE, LATEST_POSSIBLE
from htmldate.utils import decode_response, detect_encoding, fetch_url, load_html, is_dubious_html
from htmldate.validators import convert_date, date_validator, get_max_date, get_min_date, output_format_validator

from urllib3 import HTTPResponse

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
OUTPUTFORMAT = '%Y-%m-%d'

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

MOCK_PAGES = {
'http://blog.kinra.de/?p=959/': 'kinra.de.html',
'http://blog.python.org/2016/12/python-360-is-now-available.html': 'blog.python.org.html',
'http://blog.todamax.net/2018/midp-emulator-kemulator-und-brick-challenge/': 'blog.todamax.net.html',
'http://carta.info/der-neue-trend-muss-statt-wunschkoalition/': 'carta.info.html',
'https://500px.com/photo/26034451/spring-in-china-by-alexey-kruglov': '500px.com.spring.html',
'https://bayern.de/': 'bayern.de.html',
'https://creativecommons.org/about/': 'creativecommons.org.html',
'https://die-partei.net/sh/': 'die-partei.net.sh.html',
'https://en.blog.wordpress.com/': 'blog.wordpress.com.html',
'https://en.support.wordpress.com/': 'support.wordpress.com.html',
'https://futurezone.at/digital-life/wie-creativecommons-richtig-genutzt-wird/24.600.504': 'futurezone.at.cc.html',
'https://github.com/adbar/htmldate': 'github.com.html',
'https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/': 'netzpolitik.org.abmahnungen.html',
'https://pixabay.com/en/service/terms/': 'pixabay.com.tos.html',
'https://www.austria.info/': 'austria.info.html',
'https://www.befifty.de/home/2017/7/12/unter-uns-montauk': 'befifty.montauk.html',
'https://www.beltz.de/fachmedien/paedagogik/didacta_2019_in_koeln_19_23_februar/beltz_veranstaltungen_didacta_2016/veranstaltung.html?tx_news_pi1%5Bnews%5D=14392&tx_news_pi1%5Bcontroller%5D=News&tx_news_pi1%5Baction%5D=detail&cHash=10b1a32fb5b2b05360bdac257b01c8fa': 'beltz.de.didakta.html',
'https://www.channelpartner.de/a/sieben-berufe-die-zukunft-haben,3050673': 'channelpartner.de.berufe.html',
'https://www.creativecommons.at/faircoin-hackathon': 'creativecommons.at.faircoin.html',
'https://www.deutschland.de/en': 'deutschland.de.en.html',
'https://www.eff.org/files/annual-report/2015/index.html': 'eff.org.2015.html',
'https://www.facebook.com/visitaustria/': 'facebook.com.visitaustria.html',
'https://www.gnu.org/licenses/gpl-3.0.en.html': 'gnu.org.gpl.html',
'https://www.goodform.ch/blog/schattiges_plaetzchen': 'goodform.ch.blog.html',
'https://www.horizont.net/marketing/kommentare/influencer-marketing-was-sich-nach-dem-vreni-frost-urteil-aendert-und-aendern-muss-172529': 'horizont.net.html',
'https://www.intel.com/content/www/us/en/legal/terms-of-use.html': 'intel.com.tos.html',
'https://www.pferde-fuer-unsere-kinder.de/unsere-projekte/': 'pferde.projekte.de.html',
'https://www.rosneft.com/business/Upstream/Licensing/': 'rosneft.com.licensing.html',
'https://www.scs78.de/news/items/warm-war-es-schoen-war-es.html': 'scs78.de.html',
'https://www.tagesausblick.de/Analyse/USA/DOW-Jones-Jahresendrally-ade__601.html': 'tagesausblick.de.dow.html',
'https://www.transgen.de/aktuell/2687.afrikanische-schweinepest-genome-editing.html': 'transgen.de.aktuell.html',
'https://www.weltwoche.ch/ausgaben/2019-4/artikel/forbes-die-weltwoche-ausgabe-4-2019.html': 'weltwoche.ch.html',
'https://www.wunderweib.de/manuela-reimann-hochzeitsueberraschung-in-bayern-107930.html': 'wunderweib.html',
'http://unexpecteduser.blogspot.de/2011/': 'unexpecteduser.2011.html',
'http://viehbacher.com/de/spezialisierung/internationale-forderungsbeitreibung': 'viehbacher.com.forderungsbetreibung.html',
'http://www.eza.gv.at/das-ministerium/presse/aussendungen/2018/07/aussenministerin-karin-kneissl-beim-treffen-der-deutschsprachigen-aussenminister-in-luxemburg/': 'eza.gv.at.html',
'http://www.freundeskreis-videoclips.de/waehlen-sie-car-player-tipps-zur-auswahl-der-besten-car-cd-player/': 'freundeskreis-videoclips.de.html',
'http://www.greenpeace.org/international/en/campaigns/forests/asia-pacific/': 'greenpeace.org.forests.html',
'http://www.heimicke.de/chronik/zahlen-und-daten/': 'heimicke.de.zahlen.html',
'http://www.hobby-werkstatt-blog.de/arduino/424-eine-arduino-virtual-wall-fuer-den-irobot-roomba.php': 'hobby-werkstatt-blog.de.roomba.html',
'http://www.hundeverein-kreisunna.de/termine.html': 'hundeverein-kreisunna.de.html',
'http://www.hundeverein-querfurt.de/index.php?option=com_content&view=article&id=54&Itemid=50': 'hundeverein-querfurt.de.html',
'http://www.jovelstefan.de/2012/05/11/parken-in-paris/': 'jovelstefan.de.parken.html',
'http://www.klimawandel-global.de/klimaschutz/energie-sparen/elektromobilitat-der-neue-trend/': 'klimawandel-global.de.html',
'http://www.medef.com/en/content/alternative-dispute-resolution-for-antitrust-damages': 'medef.fr.dispute.html',
'http://www.pbrunst.de/news/2011/12/kein-cyberterrorismus-diesmal/': 'pbrunst.de.html',
'http://www.stuttgart.de/': 'stuttgart.de.html',
'https://paris-luttes.info/quand-on-comprend-que-les-grenades-12355': 'paris-luttes.info.html',
'https://www.brigitte.de/aktuell/riverdale--so-ehrt-die-serie-luke-perry-in-staffel-vier-11602344.html': 'brigitte.de.riverdale.html',
'https://www.ldt.de/ldtblog/fall-in-love-with-black/': 'ldt.de.fallinlove.html',
'http://www.loldf.org/spip.php?article717': 'loldf.org.html',
'https://www.beltz.de/sachbuch_ratgeber/buecher/produkt_produktdetails/37219-12_wege_zu_guter_pflege.html': 'beltz.de.12wege.html',
'https://www.oberstdorf-resort.de/interaktiv/blog/unser-kraeutergarten-wannenkopfhuette.html': 'oberstdorfresort.de.kraeuter.html',
'https://www.wienbadminton.at/news/119843/Come-Together': 'wienbadminton.at.html',
'https://blog.wikimedia.org/2018/06/28/interactive-maps-now-in-your-language/': 'blog.wikimedia.interactivemaps.html',
'https://blogs.mediapart.fr/elba/blog/260619/violences-policieres-bombe-retardement-mediatique': 'mediapart.fr.violences.html',
'https://verfassungsblog.de/the-first-decade/': 'verfassungsblog.de.decade.html',
'https://cric-grenoble.info/infos-locales/article/putsh-en-cours-a-radio-kaleidoscope-1145': 'cric-grenoble.info.radio.html',
'https://www.sebastian-kurz.at/magazin/wasserstoff-als-schluesseltechnologie': 'kurz.at.wasserstoff.html',
'https://la-bas.org/la-bas-magazine/chroniques/Didier-Porte-souhaite-la-Sante-a-Balkany': 'la-bas.org.porte.html',
'https://exporo.de/wiki/europaeische-zentralbank-ezb/': 'exporo.de.ezb.html',
'https://www.revolutionpermanente.fr/Antonin-Bernanos-en-prison-depuis-pres-de-deux-mois-en-raison-de-son-militantisme': 'revolutionpermanente.fr.antonin.html',
'http://www.wara-enforcement.org/guinee-un-braconnier-delephant-interpelle-et-condamne-a-la-peine-maximale/': 'wara-enforcement.org.guinee.html',
'https://ebene11.com/die-arbeit-mit-fremden-dwg-dateien-in-autocad': 'ebene11.com.autocad.html',
'https://www.acredis.com/schoenheitsoperationen/augenlidstraffung/': 'acredis.com.augenlidstraffung.html',
'https://www.hertie-school.org/en/debate/detail/content/whats-on-the-cards-for-von-der-leyen/': 'hertie-school.org.leyen.html',
'https://www.adac.de/rund-ums-fahrzeug/tests/kindersicherheit/kindersitztest-2018/': 'adac.de.kindersitztest.html',
'http://web.archive.org/web/20210916140120/https://www.kath.ch/die-insel-der-klosterzoeglinge/': 'archive.org.kath.ch.html',
}

MEDIACLOUD_PAGES = {
    'pagename' : 'thing.html'
}


def load_mock_page(url, dirname='cache', dictname=MOCK_PAGES):
    '''load mock page from samples'''
    with open(os.path.join(TEST_DIR, dirname, dictname[url]), 'rb') as inputf:
        return inputf.read()


def load_mediacloud_page(url):
    '''load mediacloud page from samples'''
    return load_mock_page(url, dirname='test_set', dictname=MEDIACLOUD_PAGES)


def test_input():
    '''test if loaded strings/trees are handled properly'''
    assert is_dubious_html('This is a string.') is True
    assert is_dubious_html(b'This is a string.') is True
    with pytest.raises(TypeError):
        assert load_html(123) is None
    assert load_html('<'*100) is None
    assert load_html('<html><body>XYZ</body></html>') is not None
    assert load_html(b'<html><body>XYZ</body></html>') is not None
    assert load_html(b'<'*100) is None
    assert load_html(b'<html><body>\x2f\x2e\x9f</body></html>') is not None
    assert load_html('<html><body>\x2f\x2e\x9f</body></html>'.encode('latin-1')) is not None
    assert load_html('https://httpbin.org/html') is not None
    # encoding declaration
    assert load_html('<?xml version="1.0" encoding="utf-8"?><!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/><meta http-equiv="Content-Type" content="text/html; charset=utf-8"/></head><body><p>A</p><p>B</p></body></html>') is not None
    # response decoding
    assert decode_response(b'\x1f\x8babcdef') is not None
    mock = Mock()
    mock.data = (b' ')
    assert decode_response(mock) is not None
    # find_date logic
    with pytest.raises(TypeError):
        assert find_date(None) is None
    assert find_date('<html></html>', verbose=True) is None
    # min and max date output
    assert get_min_date('2020-02-20') == datetime.date(2020, 2, 20)
    assert get_min_date(None) == datetime.date(1995, 1, 1)
    assert get_min_date('3030-30-50') == datetime.date(1995, 1, 1)
    assert get_max_date('2020-02-20') == datetime.date(2020, 2, 20)
    assert get_max_date(None) == datetime.date.today()
    assert get_max_date('3030-30-50') == datetime.date.today()


def test_sanity():
    '''Test if function arguments are interpreted and processed correctly.'''
    # XPath looking for date elements
    mytree = html.fromstring('<html><body><p>Test.</p></body></html>')
    result = examine_date_elements(mytree, '//[Error', True, OUTPUTFORMAT, MIN_DATE, LATEST_POSSIBLE)
    assert result is None
    result = examine_date_elements(mytree, '//p', True, OUTPUTFORMAT, MIN_DATE, LATEST_POSSIBLE)
    assert result is None
    # wrong field values in output format
    assert output_format_validator('%Y-%m-%d') is True
    assert output_format_validator('%M-%Y') is True
    assert output_format_validator('ABC') is False
    assert output_format_validator(123) is False
    #assert output_format_validator('%\xaa') is False
    # select_candidate()
    # ...



def test_no_date():
    '''these pages should not return any date'''
    assert find_date(load_mock_page('https://www.intel.com/content/www/us/en/legal/terms-of-use.html')) is None
    # safe search
    assert find_date(load_mock_page('https://en.support.wordpress.com/'), extensive_search=False) is None
    assert find_date(load_mock_page('https://en.support.wordpress.com/')) is None
    assert find_date('<html><body>XYZ</body></html>', outputformat='123') is None
    assert find_date('<html><body>XYZ</body></html>', url='http://www.website.com/9999/01/43/') is None


def test_exact_date():
    '''these pages should return an exact date'''
    ## HTML tree
    assert find_date('<html><head><meta property="dc:created" content="2017-09-01"/></head><body></body></html>') == '2017-09-01'
    assert find_date('<html><head><meta property="og:published_time" content="2017-09-01"/></head><body></body></html>', original_date=True) == '2017-09-01'
    assert find_date('<html><head><meta name="last-modified" content="2017-09-01"/></head><body></body></html>', original_date=False) == '2017-09-01'
    assert find_date('<html><head><meta property="OG:Updated_Time" content="2017-09-01"/></head><body></body></html>', extensive_search=False) == '2017-09-01'
    assert find_date('<html><head><Meta Property="og:updated_time" content="2017-09-01"/></head><body></body></html>', extensive_search=False) == '2017-09-01'
    assert find_date('<html><head><meta name="created" content="2017-01-09"/></head><body></body></html>') == '2017-01-09'
    assert find_date('<html><head><meta itemprop="copyrightyear" content="2017"/></head><body></body></html>') == '2017-01-01'

    # original date
    assert find_date('<html><head><meta property="OG:Updated_Time" content="2017-09-01"/><meta property="OG:Original_Time" content="2017-07-02"/></head><body></body></html>', original_date=True) == '2017-07-02'
    assert find_date('<html><head><meta property="OG:Updated_Time" content="2017-09-01"/><meta property="OG:Original_Time" content="2017-07-02"/></head><body></body></html>', original_date=False) == '2017-09-01'

    ## link in header
    assert find_date(load_mock_page('http://www.jovelstefan.de/2012/05/11/parken-in-paris/')) == '2012-05-11'

    ## meta in header
    assert find_date('<html><head><meta/></head><body></body></html>') is None
    assert find_date(load_mock_page('https://500px.com/photo/26034451/spring-in-china-by-alexey-kruglov')) == '2013-02-16'
    assert find_date('<html><head><meta name="og:url" content="http://www.example.com/2018/02/01/entrytitle"/></head><body></body></html>') == '2018-02-01'
    assert find_date('<html><head><meta itemprop="datecreated" datetime="2018-02-02"/></head><body></body></html>') == '2018-02-02'
    assert find_date('<html><head><meta itemprop="datemodified" content="2018-02-04"/></head><body></body></html>') == '2018-02-04'
    assert find_date('<html><head><meta http-equiv="last-modified" content="2018-02-05"/></head><body></body></html>') == '2018-02-05'
    assert find_date('<html><head><meta name="lastmodified" content="2018-02-05"/></head><body></body></html>', original_date=True) == '2018-02-05'
    assert find_date('<html><head><meta name="lastmodified" content="2018-02-05"/></head><body></body></html>', original_date=False) == '2018-02-05'
    assert find_date('<html><head><meta http-equiv="date" content="2017-09-01"/></head><body></body></html>', original_date=True) == '2017-09-01'
    assert find_date('<html><head><meta http-equiv="last-modified" content="2018-10-01"/><meta http-equiv="date" content="2017-09-01"/></head><body></body></html>', original_date=True) == '2017-09-01'
    assert find_date('<html><head><meta http-equiv="last-modified" content="2018-10-01"/><meta http-equiv="date" content="2017-09-01"/></head><body></body></html>', original_date=False) == '2018-10-01'
    assert find_date('<html><head><meta http-equiv="date" content="2017-09-01"/><meta http-equiv="last-modified" content="2018-10-01"/></head><body></body></html>', original_date=True) == '2017-09-01'
    assert find_date('<html><head><meta http-equiv="date" content="2017-09-01"/><meta http-equiv="last-modified" content="2018-10-01"/></head><body></body></html>', original_date=False) == '2018-10-01'
    assert find_date('<html><head><meta name="Publish_Date" content="02.02.2004"/></head><body></body></html>') == '2004-02-02'
    assert find_date('<html><head><meta name="pubDate" content="2018-02-06"/></head><body></body></html>') == '2018-02-06'
    assert find_date('<html><head><meta pubdate="pubDate" content="2018-02-06"/></head><body></body></html>') == '2018-02-06'
    assert find_date('<html><head><meta itemprop="DateModified" datetime="2018-02-06"/></head><body></body></html>') == '2018-02-06'
    assert find_date('<html><head><meta name="DC.Issued" content="2021-07-13"/></head><body></body></html>') == '2021-07-13'
    assert find_date('<html><head><meta itemprop="dateUpdate" datetime="2018-02-06"/></head><body></body></html>', original_date=True) == '2018-02-06'
    assert find_date('<html><head><meta itemprop="dateUpdate" datetime="2018-02-06"/></head><body></body></html>', original_date=False) == '2018-02-06'

    ## time in document body
    assert find_date(load_mock_page('https://www.facebook.com/visitaustria/'), original_date=True) == '2017-10-06'
    assert find_date(load_mock_page('https://www.facebook.com/visitaustria/'), original_date=False) == '2017-10-08'
    assert find_date(load_mock_page('http://www.medef.com/en/content/alternative-dispute-resolution-for-antitrust-damages')) == '2017-09-01'
    assert find_date('<html><body><time datetime="08:00"></body></html>') is None
    assert find_date('<html><body><time datetime="2014-07-10 08:30:45.687"></body></html>') == '2014-07-10'
    assert find_date('<html><head></head><body><time class="entry-time" itemprop="datePublished" datetime="2018-04-18T09:57:38+00:00"></body></html>') == '2018-04-18'
    assert find_date('<html><body><footer class="article-footer"><p class="byline">Veröffentlicht am <time class="updated" datetime="2019-01-03T14:56:51+00:00">3. Januar 2019 um 14:56 Uhr.</time></p></footer></body></html>') == '2019-01-03'
    assert find_date('<html><body><footer class="article-footer"><p class="byline">Veröffentlicht am <time class="updated" datetime="2019-01-03T14:56:51+00:00"></time></p></footer></body></html>') == '2019-01-03'
    assert find_date('<html><body><time datetime="2011-09-27" class="entry-date"></time><time datetime="2011-09-28" class="updated"></time></body></html>', original_date=True) == '2011-09-27'
    # problem here:
    #assert find_date('<html><body><time datetime="2011-09-27" class="entry-date"></time><time datetime="2011-09-28" class="updated"></time></body></html>', original_date=False) == '2011-09-28'
    #assert find_date('<html><body><time datetime="2011-09-28" class="updated"></time><time datetime="2011-09-27" class="entry-date"></time></body></html>', original_date=True) == '2011-09-27'
    assert find_date('<html><body><time datetime="2011-09-28" class="updated"></time><time datetime="2011-09-27" class="entry-date"></time></body></html>', original_date=False) == '2011-09-28'
    # removed from HTML5 https://www.w3schools.com/TAgs/att_time_datetime_pubdate.asp
    assert find_date('<html><body><time datetime="2011-09-28" pubdate="pubdate"></time></body></html>', original_date=False) == '2011-09-28'
    assert find_date('<html><body><time datetime="2011-09-28" pubdate="pubdate"></time></body></html>', original_date=True) == '2011-09-28'
    assert find_date('<html><body><time datetime="2011-09-28" class="entry-date"></time></body></html>', original_date=True) == '2011-09-28'

    ## precise pattern in document body
    assert find_date('<html><body><font size="2" face="Arial,Geneva,Helvetica">Bei <a href="../../sonstiges/anfrage.php"><b>Bestellungen</b></a> bitte Angabe der Titelnummer nicht vergessen!<br><br>Stand: 03.04.2019</font></body></html>') == '2019-04-03'
    assert find_date('<html><body><div>Erstausstrahlung: 01.01.2020</div><div>Preisstand: 03.02.2022 03:00 GMT+1</div></body></html>') == '2022-02-03'
    assert find_date('<html><body>Datum: 10.11.2017</body></html>') == '2017-11-10'
    assert find_date(load_mock_page('https://www.tagesausblick.de/Analyse/USA/DOW-Jones-Jahresendrally-ade__601.html')) == '2012-12-22'
    assert find_date(load_mock_page('http://blog.todamax.net/2018/midp-emulator-kemulator-und-brick-challenge/')) == '2018-02-15'
    # JSON datePublished
    assert find_date(load_mock_page('https://www.acredis.com/schoenheitsoperationen/augenlidstraffung/'), original_date=True) == '2018-02-28'
    # JSON dateModified
    assert find_date(load_mock_page('https://www.channelpartner.de/a/sieben-berufe-die-zukunft-haben,3050673'), original_date=False) == '2019-04-03'

    ## meta in document body
    assert find_date(load_mock_page('https://futurezone.at/digital-life/wie-creativecommons-richtig-genutzt-wird/24.600.504'), original_date=True) == '2013-08-09'
    assert find_date(load_mock_page('https://www.horizont.net/marketing/kommentare/influencer-marketing-was-sich-nach-dem-vreni-frost-urteil-aendert-und-aendern-muss-172529')) == '2019-01-29'
    assert find_date(load_mock_page('http://www.klimawandel-global.de/klimaschutz/energie-sparen/elektromobilitat-der-neue-trend/')) == '2013-05-03'
    assert find_date(load_mock_page('http://www.hobby-werkstatt-blog.de/arduino/424-eine-arduino-virtual-wall-fuer-den-irobot-roomba.php')) == '2015-12-14'
    assert find_date(load_mock_page('https://www.beltz.de/fachmedien/paedagogik/didacta_2019_in_koeln_19_23_februar/beltz_veranstaltungen_didacta_2016/veranstaltung.html?tx_news_pi1%5Bnews%5D=14392&tx_news_pi1%5Bcontroller%5D=News&tx_news_pi1%5Baction%5D=detail&cHash=10b1a32fb5b2b05360bdac257b01c8fa')) == '2019-02-20'
    assert find_date(load_mock_page('https://www.wienbadminton.at/news/119843/Come-Together'), extensive_search=False) is None
    assert find_date(load_mock_page('https://www.wienbadminton.at/news/119843/Come-Together'), extensive_search=True) == '2018-05-06'

    # abbr in document body
    assert find_date(load_mock_page('http://blog.kinra.de/?p=959/')) == '2012-12-16'
    assert find_date('<html><body><abbr class="published">am 12.11.16</abbr></body></html>', original_date=False) == '2016-11-12'
    assert find_date('<html><body><abbr class="published">am 12.11.16</abbr></body></html>', original_date=True) == '2016-11-12'
    assert find_date('<html><body><abbr class="published" title="2016-11-12">XYZ</abbr></body></html>', original_date=True) == '2016-11-12'
    assert find_date('<html><body><abbr class="date-published">8.11.2016</abbr></body></html>') == '2016-11-08'
    # valid vs. invalid data-utime
    assert find_date('<html><body><abbr data-utime="1438091078" class="something">A date</abbr></body></html>') == '2015-07-28'
    assert find_date('<html><body><abbr data-utime="143809-1078" class="something">A date</abbr></body></html>') is None

    # time in document body
    assert find_date('<html><body><time>2018-01-04</time></body></html>') == '2018-01-04'
    assert find_date(load_mock_page('https://www.adac.de/rund-ums-fahrzeug/tests/kindersicherheit/kindersitztest-2018/')) == '2018-10-23'

    # additional XPath expressions
    assert find_date('<html><body><div class="fecha">2018-01-04</div></body></html>') == '2018-01-04'

    ## other expressions in document body
    assert find_date('<html><body>"datePublished":"2018-01-04"</body></html>') == '2018-01-04'
    assert find_date('<html><body>Stand: 1.4.18</body></html>') == '2018-04-01'
    assert find_date(load_mock_page('http://www.stuttgart.de/')) == '2017-10-09'

    ## in document body
    assert find_date(load_mock_page('https://github.com/adbar/htmldate')) == '2019-01-01'
    #assert find_date(load_mock_page('https://github.com/adbar/htmldate'), original_date=True) == '2016-07-12'

    assert find_date(load_mock_page('https://en.blog.wordpress.com/')) == '2017-08-30'
    assert find_date(load_mock_page('https://www.austria.info/')) == '2017-09-07'
    assert find_date(load_mock_page('https://www.eff.org/files/annual-report/2015/index.html')) == '2016-05-04'
    assert find_date(load_mock_page('http://unexpecteduser.blogspot.de/2011/')) == '2011-03-30'
    assert find_date(load_mock_page('https://die-partei.net/sh/')) == '2014-07-19'
    assert find_date(load_mock_page('https://www.rosneft.com/business/Upstream/Licensing/')) == '2017-02-27' # most probably 2014-12-31, found in text
    assert find_date(load_mock_page('http://www.freundeskreis-videoclips.de/waehlen-sie-car-player-tipps-zur-auswahl-der-besten-car-cd-player/')) == '2017-07-12'
    assert find_date(load_mock_page('https://www.scs78.de/news/items/warm-war-es-schoen-war-es.html')) == '2018-06-10'
    assert find_date(load_mock_page('https://www.goodform.ch/blog/schattiges_plaetzchen')) == '2018-06-27'
    assert find_date(load_mock_page('https://www.transgen.de/aktuell/2687.afrikanische-schweinepest-genome-editing.html')) == '2018-01-18'
    assert find_date(load_mock_page('http://www.eza.gv.at/das-ministerium/presse/aussendungen/2018/07/aussenministerin-karin-kneissl-beim-treffen-der-deutschsprachigen-aussenminister-in-luxemburg/')) == '2018-07-03'
    assert find_date(load_mock_page('https://www.weltwoche.ch/ausgaben/2019-4/artikel/forbes-die-weltwoche-ausgabe-4-2019.html')) == '2019-01-23'
    # free text
    assert find_date('<html><body>&copy; 2017</body></html>') == '2017-01-01'
    assert find_date('<html><body>© 2017</body></html>') == '2017-01-01'
    assert find_date('<html><body><p>Dieses Datum ist leider ungültig: 30. Februar 2018.</p></body></html>', extensive_search=False) is None
    assert find_date('<html><body><p>Dieses Datum ist leider ungültig: 30. Februar 2018.</p></body></html>') == '2018-01-01'
    # other format
    assert find_date(load_mock_page('http://unexpecteduser.blogspot.de/2011/'), outputformat='%d %B %Y') == '30 March 2011'
    assert find_date(load_mock_page('http://blog.python.org/2016/12/python-360-is-now-available.html'), outputformat='%d %B %Y') == '23 December 2016'

    # additional list
    assert find_date(load_mock_page('http://carta.info/der-neue-trend-muss-statt-wunschkoalition/')) == '2012-05-08'
    assert find_date(load_mock_page('https://www.wunderweib.de/manuela-reimann-hochzeitsueberraschung-in-bayern-107930.html')) == '2019-06-20'
    assert find_date(load_mock_page('https://www.befifty.de/home/2017/7/12/unter-uns-montauk')) == '2017-07-12'
    assert find_date(load_mock_page('https://www.brigitte.de/aktuell/riverdale--so-ehrt-die-serie-luke-perry-in-staffel-vier-11602344.html')) == '2019-06-20' #returns an error
    assert find_date(load_mock_page('http://www.loldf.org/spip.php?article717')) == '2019-06-27'
    assert find_date(load_mock_page('https://www.beltz.de/sachbuch_ratgeber/buecher/produkt_produktdetails/37219-12_wege_zu_guter_pflege.html')) == '2019-02-07'
    assert find_date(load_mock_page('https://www.oberstdorf-resort.de/interaktiv/blog/unser-kraeutergarten-wannenkopfhuette.html')) == '2018-06-20'
    assert find_date(load_mock_page('https://www.wienbadminton.at/news/119843/Come-Together')) == '2018-05-06'
    assert find_date(load_mock_page('https://www.ldt.de/ldtblog/fall-in-love-with-black/')) == '2017-08-08'
    assert find_date(load_mock_page('https://paris-luttes.info/quand-on-comprend-que-les-grenades-12355'), original_date=True) == '2019-06-29'
    assert find_date(load_mock_page('https://verfassungsblog.de/the-first-decade/')) == '2019-07-13'
    assert find_date(load_mock_page('https://cric-grenoble.info/infos-locales/article/putsh-en-cours-a-radio-kaleidoscope-1145')) == '2019-06-09'
    assert find_date(load_mock_page('https://www.sebastian-kurz.at/magazin/wasserstoff-als-schluesseltechnologie')) == '2019-07-30'
    assert find_date(load_mock_page('https://exporo.de/wiki/europaeische-zentralbank-ezb/')) == '2018-01-01'
    # only found by extensive search
    assert(find_date(load_mock_page('https://ebene11.com/die-arbeit-mit-fremden-dwg-dateien-in-autocad'), extensive_search=False)) is None
    assert(find_date(load_mock_page('https://ebene11.com/die-arbeit-mit-fremden-dwg-dateien-in-autocad'), extensive_search=True)) == '2017-01-12'
    assert(find_date(load_mock_page('https://www.hertie-school.org/en/debate/detail/content/whats-on-the-cards-for-von-der-leyen/'), extensive_search=False)) is None
    assert(find_date(load_mock_page('https://www.hertie-school.org/en/debate/detail/content/whats-on-the-cards-for-von-der-leyen/'), extensive_search=True)) == '2019-12-02' # 2019-02-12?

    # date not in footer but at the start of the article
    assert find_date(load_mock_page('http://www.wara-enforcement.org/guinee-un-braconnier-delephant-interpelle-et-condamne-a-la-peine-maximale/')) == '2016-09-27'

    # URL in IMG
    # header
    assert find_date('<html><meta property="og:image" content="https://example.org/img/2019-05-05/test.jpg"><body></body></html>') == '2019-05-05'
    assert find_date('<html><meta property="og:image" content="https://example.org/img/test.jpg"><body></body></html>') is None
    # body
    assert find_date('<html><body><img src="https://example.org/img/2019-05-05/test.jpg"/></body></html>') == '2019-05-05'
    assert find_date('<html><body><img src="https://example.org/img/test.jpg"/></body></html>') is None
    assert find_date('<html><body><img src="https://example.org/img/2019-05-03/test.jpg"/><img src="https://example.org/img/2019-05-04/test.jpg"/><img src="https://example.org/img/2019-05-05/test.jpg"/></body></html>') == '2019-05-05'
    assert find_date('<html><body><img src="https://example.org/img/2019-05-05/test.jpg"/><img src="https://example.org/img/2019-05-04/test.jpg"/><img src="https://example.org/img/2019-05-03/test.jpg"/></body></html>') == '2019-05-05'
    # in title
    assert find_date('<html><head><title>Bericht zur Coronalage vom 22.04.2020 – worauf wartet die Politik? – DIE ACHSE DES GUTEN. ACHGUT.COM</title></head></html>') == '2020-04-22'
    # in unknown div
    assert find_date('<html><body><div class="spip spip-block-right" style="text-align:right;">Le 26 juin 2019</div></body></html>', extensive_search=False) is None
    assert find_date('<html><body><div class="spip spip-block-right" style="text-align:right;">Le 26 juin 2019</div></body></html>', extensive_search=True) == '2019-06-26'
    # in link title
    assert find_date('<html><body><a class="ribbon date " title="12th December 2018" href="https://example.org/" itemprop="url">Text</a></body></html>') == '2018-12-12'


    # archive.org documents
    assert find_date(load_mock_page('http://web.archive.org/web/20210916140120/https://www.kath.ch/die-insel-der-klosterzoeglinge/'), extensive_search=False) is None
    assert find_date(load_mock_page('http://web.archive.org/web/20210916140120/https://www.kath.ch/die-insel-der-klosterzoeglinge/'), extensive_search=True) == '2021-07-13'


def test_approximate_date():
    '''this page should return an approximate date'''
    # copyright text
    assert find_date(load_mock_page('http://viehbacher.com/de/spezialisierung/internationale-forderungsbeitreibung')) == '2016-01-01' # somewhere in 2016
    # other
    assert find_date(load_mock_page('https://creativecommons.org/about/'), original_date=False) == '2017-08-11' # or '2017-08-03'
    assert find_date(load_mock_page('https://creativecommons.org/about/'), original_date=True) == '2016-05-22' # or '2017-08-03'
    assert find_date(load_mock_page('https://www.deutschland.de/en')) == '2017-08-01'
    assert find_date(load_mock_page('http://www.greenpeace.org/international/en/campaigns/forests/asia-pacific/')) == '2017-04-28'
    assert find_date(load_mock_page('https://www.creativecommons.at/faircoin-hackathon')) == '2017-07-24'
    assert find_date(load_mock_page('https://pixabay.com/en/service/terms/')) == '2017-08-09'
    assert find_date(load_mock_page('https://bayern.de/'),) == '2017-10-06' # most probably 2017-10-06
    assert find_date(load_mock_page('https://www.pferde-fuer-unsere-kinder.de/unsere-projekte/')) == '2016-07-20' # most probably 2016-07-15
    # LXML bug filed: https://bugs.launchpad.net/lxml/+bug/1955915
    #assert find_date(load_mock_page('http://www.hundeverein-querfurt.de/index.php?option=com_content&view=article&id=54&Itemid=50'), original_date=False) == '2016-12-04' # 2010-11-01 in meta, 2016 more plausible
    assert find_date(load_mock_page('http://www.pbrunst.de/news/2011/12/kein-cyberterrorismus-diesmal/'), original_date=False) == '2011-12-01'
    ## TODO: problem, take URL instead
    assert find_date(load_mock_page('http://www.pbrunst.de/news/2011/12/kein-cyberterrorismus-diesmal/'), original_date=True) == '2010-06-01'
    # dates in table
    assert find_date(load_mock_page('http://www.hundeverein-kreisunna.de/termine.html')) == '2017-03-29' # probably newer


def test_date_validator():
    '''test internal date validation'''
    assert date_validator('2016-01-01', OUTPUTFORMAT) is True
    assert date_validator('1998-08-08', OUTPUTFORMAT) is True
    assert date_validator('2001-12-31', OUTPUTFORMAT) is True
    assert date_validator('1992-07-30', OUTPUTFORMAT) is False
    assert date_validator('1901-13-98', OUTPUTFORMAT) is False
    assert date_validator('202-01', OUTPUTFORMAT) is False
    assert date_validator('1922', '%Y') is False
    assert date_validator('2004', '%Y') is True


def test_convert_date():
    '''test date conversion'''
    assert convert_date('2016-11-18', '%Y-%m-%d', '%d %B %Y') == '18 November 2016'
    assert convert_date('18 November 2016', '%d %B %Y', '%Y-%m-%d') == '2016-11-18'



def test_try_ymd_date():
    '''test date extraction via external package'''
    find_date.extensive_search = False
    assert try_ymd_date('Fri, Sept 1, 2017', OUTPUTFORMAT, False, MIN_DATE, LATEST_POSSIBLE) is None
    find_date.extensive_search = True
    assert try_ymd_date('Friday, September 01, 2017', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) == '2017-09-01'
    assert try_ymd_date('Fr, 1 Sep 2017 16:27:51 MESZ', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) == '2017-09-01'
    assert try_ymd_date('Freitag, 01. September 2017', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) == '2017-09-01'
    assert try_ymd_date('Am 1. September 2017 um 15:36 Uhr schrieb', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) == '2017-09-01'
    assert try_ymd_date('Fri - September 1 - 2017', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) == '2017-09-01'
    assert try_ymd_date('1.9.2017', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) == '2017-09-01'
    assert try_ymd_date('1/9/17', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) == '2017-09-01' # assuming MDY format
    assert try_ymd_date('201709011234', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) == '2017-09-01'
    # other output format
    assert try_ymd_date('1.9.2017', '%d %B %Y', True, MIN_DATE, LATEST_POSSIBLE) == '01 September 2017'
    # wrong
    assert try_ymd_date('201', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) is None
    assert try_ymd_date('14:35:10', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) is None
    assert try_ymd_date('12:00 h', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) is None
    # date range
    assert try_ymd_date('2005-2006', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) is None


# def test_header():
#    assert examine_header(tree, OUTPUTFORMAT, PARSER)


def test_compare_reference(extensive_search=False, original_date=False, min_date=MIN_DATE, max_date=LATEST_POSSIBLE):
    '''test comparison function'''
    assert compare_reference(0, 'AAAA', OUTPUTFORMAT, extensive_search, original_date, min_date, max_date) == 0
    assert compare_reference(1517500000, '2018-33-01', OUTPUTFORMAT, extensive_search, original_date, min_date, max_date) == 1517500000
    assert 1517400000 < compare_reference(0, '2018-02-01', OUTPUTFORMAT, extensive_search, original_date, min_date, max_date) < 1517500000
    assert compare_reference(1517500000, '2018-02-01', OUTPUTFORMAT, extensive_search, original_date, min_date, max_date) == 1517500000


def test_candidate_selection(min_date=MIN_DATE, max_date=LATEST_POSSIBLE):
    '''test the algorithm for several candidates'''
    original_date = False
    # patterns
    catch = re.compile(r'([0-9]{4})-([0-9]{2})-([0-9]{2})')
    yearpat = re.compile(r'^([0-9]{4})')
    # nonsense
    allmatches = ['20208956', '20208956', '20208956', '19018956', '209561', '22020895607-12', '2-28']
    occurrences = Counter(allmatches)
    result = select_candidate(occurrences, catch, yearpat, original_date, min_date, max_date)
    assert result is None
    # plausible
    allmatches = ['2016-12-23', '2016-12-23', '2016-12-23', '2016-12-23', '2017-08-11', '2016-07-12', '2017-11-28']
    occurrences = Counter(allmatches)
    result = select_candidate(occurrences, catch, yearpat, original_date, min_date, max_date)
    assert result.group(0) == '2017-11-28'
    original_date = True
    result = select_candidate(occurrences, catch, yearpat, original_date, min_date, max_date)
    assert result.group(0) == '2016-07-12'
    # mix plausible/implausible
    allmatches = ['2116-12-23', '2116-12-23', '2116-12-23', '2017-08-11', '2017-08-11']
    occurrences = Counter(allmatches)
    result = select_candidate(occurrences, catch, yearpat, original_date, min_date, max_date)
    assert result.group(0) == '2017-08-11'
    original_date = False
    allmatches = ['2116-12-23', '2116-12-23', '2116-12-23', '2017-08-11', '2017-08-11']
    occurrences = Counter(allmatches)
    result = select_candidate(occurrences, catch, yearpat, original_date, min_date, max_date)
    assert result.group(0) == '2017-08-11'


def test_regex_parse():
    '''test date extraction using rules and regular expressions'''
    assert regex_parse('3. Dezember 2008') is not None
    assert regex_parse('33. Dezember 2008') is None
    assert regex_parse('3 Aralık 2008 Çarşamba') is not None
    assert regex_parse('3 Aralık 2008') is not None
    assert regex_parse('Tuesday, March 26th, 2019') is not None
    assert regex_parse('March 26, 2019') is not None
    assert regex_parse('3rd Tuesday in March') is None
    assert regex_parse('Mart 26, 2019') is not None
    assert regex_parse('Salı, Mart 26, 2019') is not None
    assert regex_parse('36/14/2016') is None
    assert regex_parse('January 36 1998') is None
    assert custom_parse('January 12 1098', OUTPUTFORMAT, False, MIN_DATE, LATEST_POSSIBLE) is None
    assert custom_parse('1998-01', OUTPUTFORMAT, False, MIN_DATE, LATEST_POSSIBLE) is not None
    assert custom_parse('10.10.98', OUTPUTFORMAT, False, MIN_DATE, LATEST_POSSIBLE) is not None
    assert custom_parse('12122004', OUTPUTFORMAT, False, MIN_DATE, LATEST_POSSIBLE) is None
    assert custom_parse('3/14/2016', OUTPUTFORMAT, False, MIN_DATE, LATEST_POSSIBLE) is not None
    assert custom_parse('20041212', OUTPUTFORMAT, False, MIN_DATE, LATEST_POSSIBLE) is not None
    assert custom_parse('20041212', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) is not None
    assert custom_parse('1212-20-04', OUTPUTFORMAT, False, MIN_DATE, LATEST_POSSIBLE) is None
    assert custom_parse('1212-20-04', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) is None
    assert custom_parse('2004-12-12', OUTPUTFORMAT, False, MIN_DATE, LATEST_POSSIBLE) is not None
    assert custom_parse('2004-12-12', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) is not None
    assert custom_parse('33.20.2004', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) is None
    assert custom_parse('12.12.2004', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) is not None
    assert custom_parse('2019 28 meh', OUTPUTFORMAT, False, MIN_DATE, LATEST_POSSIBLE) is None
    assert custom_parse('2019 28 meh', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) is None
    # regex-based matches
    assert custom_parse('abcd 20041212 efgh', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) is not None
    assert custom_parse('abcd 2004-2-12 efgh', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) is not None
    assert custom_parse('abcd 2004-2 efgh', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) is not None
    assert custom_parse('abcd 2004-2 efgh', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) is not None
    assert custom_parse('abcd 32. Januar 2020 efgh', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) is None
    #for Nones caused by newlines and duplicates
    assert regex_parse("January 1st, 1998") is not None
    assert regex_parse("February 1st, 1998") is not None
    assert regex_parse("March 1st, 1998") is not None
    assert regex_parse("April 1st, 1998") is not None
    assert regex_parse("May 1st, 1998") is not None
    assert regex_parse("June 1st, 1998") is not None
    assert regex_parse("July 1st, 1998") is not None
    assert regex_parse("August 1st, 1998") is not None
    assert regex_parse("September 1st, 1998") is not None
    assert regex_parse("October 1st, 1998") is not None
    assert regex_parse("November 1st, 1998") is not None
    assert regex_parse("December 1st, 1998") is not None
    assert regex_parse("Jan 1st, 1998") is not None
    assert regex_parse("Feb 1st, 1998") is not None
    assert regex_parse("Mar 1st, 1998") is not None
    assert regex_parse("Apr 1st, 1998") is not None
    assert regex_parse("Jun 1st, 1998") is not None
    assert regex_parse("Jul 1st, 1998") is not None
    assert regex_parse("Aug 1st, 1998") is not None
    assert regex_parse("Sep 1st, 1998") is not None
    assert regex_parse("Oct 1st, 1998") is not None
    assert regex_parse("Nov 1st, 1998") is not None
    assert regex_parse("Dec 1st, 1998") is not None
    assert regex_parse("Januar 1, 1998") is not None
    assert regex_parse("Jänner 1, 1998") is not None
    assert regex_parse("Februar 1, 1998") is not None
    assert regex_parse("Feber 1, 1998") is not None
    assert regex_parse("März 1, 1998") is not None
    assert regex_parse("April 1, 1998") is not None
    assert regex_parse("Mai 1, 1998") is not None
    assert regex_parse("Juni 1, 1998") is not None
    assert regex_parse("Juli 1, 1998") is not None
    assert regex_parse("August 1, 1998") is not None
    assert regex_parse("September 1, 1998") is not None
    assert regex_parse("Oktober 1, 1998") is not None
    assert regex_parse("November 1, 1998") is not None
    assert regex_parse("Dezember 1, 1998") is not None
    assert regex_parse("Ocak 1, 1998") is not None
    assert regex_parse("Şubat 1, 1998") is not None
    assert regex_parse("Mart 1, 1998") is not None
    assert regex_parse("Nisan 1, 1998") is not None
    assert regex_parse("Mayıs 1, 1998") is not None
    assert regex_parse("Haziran 1, 1998") is not None
    assert regex_parse("Temmuz 1, 1998") is not None
    assert regex_parse("Ağustos 1, 1998") is not None
    assert regex_parse("Eylül 1, 1998") is not None
    assert regex_parse("Ekim 1, 1998") is not None
    assert regex_parse("Kasım 1, 1998") is not None
    assert regex_parse("Aralık 1, 1998") is not None
    assert regex_parse("Oca 1, 1998") is not None
    assert regex_parse("Şub 1, 1998") is not None
    assert regex_parse("Mar 1, 1998") is not None
    assert regex_parse("Nis 1, 1998") is not None
    assert regex_parse("May 1, 1998") is not None
    assert regex_parse("Haz 1, 1998") is not None
    assert regex_parse("Tem 1, 1998") is not None
    assert regex_parse("Ağu 1, 1998") is not None
    assert regex_parse("Eyl 1, 1998") is not None
    assert regex_parse("Eki 1, 1998") is not None
    assert regex_parse("Kas 1, 1998") is not None
    assert regex_parse("Ara 1, 1998") is not None
    assert regex_parse("1 January 1998") is not None
    assert regex_parse("1 February 1998") is not None
    assert regex_parse("1 March 1998") is not None
    assert regex_parse("1 April 1998") is not None
    assert regex_parse("1 May 1998") is not None
    assert regex_parse("1 June 1998") is not None
    assert regex_parse("1 July 1998") is not None
    assert regex_parse("1 August 1998") is not None
    assert regex_parse("1 September 1998") is not None
    assert regex_parse("1 October 1998") is not None
    assert regex_parse("1 November 1998") is not None
    assert regex_parse("1 December 1998") is not None
    assert regex_parse("1 Jan 1998") is not None
    assert regex_parse("1 Feb 1998") is not None
    assert regex_parse("1 Mar 1998") is not None
    assert regex_parse("1 Apr 1998") is not None
    assert regex_parse("1 Jun 1998") is not None
    assert regex_parse("1 Jul 1998") is not None
    assert regex_parse("1 Aug 1998") is not None
    assert regex_parse("1 Sep 1998") is not None
    assert regex_parse("1 Oct 1998") is not None
    assert regex_parse("1 Nov 1998") is not None
    assert regex_parse("1 Dec 1998") is not None
    assert regex_parse("1 Januar 1998") is not None
    assert regex_parse("1 Jänner 1998") is not None
    assert regex_parse("1 Februar 1998") is not None
    assert regex_parse("1 Feber 1998") is not None
    assert regex_parse("1 März 1998") is not None
    assert regex_parse("1 April 1998") is not None
    assert regex_parse("1 Mai 1998") is not None
    assert regex_parse("1 Juni 1998") is not None
    assert regex_parse("1 Juli 1998") is not None
    assert regex_parse("1 August 1998") is not None
    assert regex_parse("1 September 1998") is not None
    assert regex_parse("1 Oktober 1998") is not None
    assert regex_parse("1 November 1998") is not None
    assert regex_parse("1 Dezember 1998") is not None
    assert regex_parse("1 Ocak 1998") is not None
    assert regex_parse("1 Şubat 1998") is not None
    assert regex_parse("1 Mart 1998") is not None
    assert regex_parse("1 Nisan 1998") is not None
    assert regex_parse("1 Mayıs 1998") is not None
    assert regex_parse("1 Haziran 1998") is not None
    assert regex_parse("1 Temmuz 1998") is not None
    assert regex_parse("1 Ağustos 1998") is not None
    assert regex_parse("1 Eylül 1998") is not None
    assert regex_parse("1 Ekim 1998") is not None
    assert regex_parse("1 Kasım 1998") is not None
    assert regex_parse("1 Aralık 1998") is not None
    assert regex_parse("1 Oca 1998") is not None
    assert regex_parse("1 Şub 1998") is not None
    assert regex_parse("1 Mar 1998") is not None
    assert regex_parse("1 Nis 1998") is not None
    assert regex_parse("1 May 1998") is not None
    assert regex_parse("1 Haz 1998") is not None
    assert regex_parse("1 Tem 1998") is not None
    assert regex_parse("1 Ağu 1998") is not None
    assert regex_parse("1 Eyl 1998") is not None
    assert regex_parse("1 Eki 1998") is not None
    assert regex_parse("1 Kas 1998") is not None
    assert regex_parse("1 Ara 1998") is not None


def test_external_date_parser():
    '''test external date parser'''
    assert external_date_parser('Wednesday, January 1st 2020', OUTPUTFORMAT) == '2020-01-01'
    assert external_date_parser('Random text with 2020', OUTPUTFORMAT) is None


def test_url():
    '''test url parameter'''
    assert find_date('<html><body><p>Aaa, bbb.</p></body></html>', url='http://example.com/category/2016/07/12/key-words') == '2016-07-12'
    assert find_date('<html><body><p>Aaa, bbb.</p></body></html>', url='http://example.com/2016/key-words') is None
    assert find_date('<html><body><p>Aaa, bbb.</p></body></html>', url='http://www.kreditwesen.org/widerstand-berlin/2012-11-29/keine-kurzung-bei-der-jugend-klubs-konnen-vorerst-aufatmen-bvv-beschliest-haushaltsplan/') == '2012-11-29'
    assert find_date('<html><body><p>Aaa, bbb.</p></body></html>', url='http://www.kreditwesen.org/widerstand-berlin/2012-11/keine-kurzung-bei-der-jugend-klubs-konnen-vorerst-aufatmen-bvv-beschliest-haushaltsplan/') is None
    assert find_date('<html><body><p>Aaa, bbb.</p></body></html>', url='http://www.kreditwesen.org/widerstand-berlin/6666-42-87/') is None
    assert find_date('<html><body><p>Z.</p></body></html>', url='https://www.pamelaandersonfoundation.org/news/2019/6/26/dm4wjh7skxerzzw8qa8cklj8xdri5j') == '2019-06-26'
    assert extract_partial_url_date('https://testsite.org/2018/01/test', '%Y-%m-%d') == '2018-01-01'
    assert extract_partial_url_date('https://testsite.org/2018/33/test', '%Y-%m-%d') is None


def test_approximate_url():
    '''test url parameter'''
    assert find_date('<html><body><p>Aaa, bbb.</p></body></html>', url='http://example.com/blog/2016/07/key-words') == '2016-07-01'
    assert find_date('<html><body><p>Aaa, bbb.</p></body></html>', url='http://example.com/category/2016/') is None


def test_search_pattern(original_date=False, min_date=MIN_DATE, max_date=LATEST_POSSIBLE):
    '''test pattern search in strings'''
    #
    pattern = re.compile(r'\D([0-9]{4}[/.-][0-9]{2})\D')
    catch = re.compile(r'([0-9]{4})[/.-]([0-9]{2})')
    yearpat = re.compile(r'^([12][0-9]{3})')
    assert search_pattern('It happened on the 202.E.19, the day when it all began.', pattern, catch, yearpat, original_date, min_date, max_date) is None
    assert search_pattern('The date is 2002.02.15.', pattern, catch, yearpat, original_date, min_date, max_date) is not None
    assert search_pattern('http://www.url.net/index.html', pattern, catch, yearpat, original_date, min_date, max_date) is None
    assert search_pattern('http://www.url.net/2016/01/index.html', pattern, catch, yearpat, original_date, min_date, max_date) is not None
    #
    pattern = re.compile(r'\D([0-9]{2}[/.-][0-9]{4})\D')
    catch = re.compile(r'([0-9]{2})[/.-]([0-9]{4})')
    yearpat = re.compile(r'([12][0-9]{3})$')
    assert search_pattern('It happened on the 202.E.19, the day when it all began.', pattern, catch, yearpat, original_date, min_date, max_date) is None
    assert search_pattern('It happened on the 15.02.2002, the day when it all began.', pattern, catch, yearpat, original_date, min_date, max_date) is not None
    #
    pattern = re.compile(r'\D(2[01][0-9]{2})\D')
    catch = re.compile(r'(2[01][0-9]{2})')
    yearpat = re.compile(r'^(2[01][0-9]{2})')
    assert search_pattern('It happened in the film 300.', pattern, catch, yearpat, original_date, min_date, max_date) is None
    assert search_pattern('It happened in 2002.', pattern, catch, yearpat, original_date, min_date, max_date) is not None


def test_search_html(original_date=False, min_date=MIN_DATE, max_date=LATEST_POSSIBLE):
    '''test pattern search in HTML'''
    # file input + output format
    fileinput = load_mock_page('http://www.heimicke.de/chronik/zahlen-und-daten/')
    encoding = detect_encoding(fileinput)[0]
    assert search_page(fileinput.decode(encoding), '%d %B %Y', original_date, min_date, max_date) == '06 April 2019'
    # tree input
    assert search_page('<html><body><p>The date is 5/2010</p></body></html>', OUTPUTFORMAT, original_date, min_date, max_date) == '2010-05-01'
    assert search_page('<html><body><p>The date is 5.5.2010</p></body></html>', OUTPUTFORMAT, original_date, min_date, max_date) == '2010-05-05'
    assert search_page('<html><body><p>The date is 11/10/99</p></body></html>', OUTPUTFORMAT, original_date, min_date, max_date) == '1999-10-11'
    assert search_page('<html><body><p>The date is 3/3/11</p></body></html>', OUTPUTFORMAT, original_date, min_date, max_date) == '2011-03-03'
    assert search_page('<html><body><p>The date is 06.12.06</p></body></html>', OUTPUTFORMAT, original_date, min_date, max_date) == '2006-12-06'
    assert search_page('<html><body><p>The timestamp is 20140915D15:23H</p></body></html>', OUTPUTFORMAT, original_date, min_date, max_date) == '2014-09-15'
    assert search_page('<html><body><p>It could be 2015-04-30 or 2003-11-24.</p></body></html>', OUTPUTFORMAT, True, min_date, max_date) == '2003-11-24'
    assert search_page('<html><body><p>It could be 2015-04-30 or 2003-11-24.</p></body></html>', OUTPUTFORMAT, False, min_date, max_date) == '2015-04-30'
    assert search_page('<html><body><p>It could be 03/03/2077 or 03/03/2013.</p></body></html>', OUTPUTFORMAT, original_date, min_date, max_date) == '2013-03-03'
    assert search_page('<html><body><p>It could not be 03/03/2077 or 03/03/1988.</p></body></html>', OUTPUTFORMAT, original_date, min_date, max_date) is None
    assert search_page('<html><body><p>© The Web Association 2013.</p></body></html>', OUTPUTFORMAT, original_date, min_date, max_date) == '2013-01-01'
    assert search_page('<html><body><p>Next © Copyright 2018</p></body></html>', OUTPUTFORMAT, original_date, min_date, max_date) == '2018-01-01'
    assert search_page('<html><body><p> © Company 2014-2019 </p></body></html>', OUTPUTFORMAT, original_date, min_date, max_date) == '2019-01-01'


def test_idiosyncrasies():
    assert find_date('<html><body><p><em>Last updated: 5/5/20</em></p></body></html>') == '2020-05-05'
    assert find_date('<html><body><p><em>Last updated: 01/23/2021</em></p></body></html>') == '2021-01-23'
    assert find_date('<html><body><p><em>Published: 5/5/2020</em></p></body></html>') == '2020-05-05'
    assert find_date('<html><body><p><em>Published in: 05.05.2020</em></p></body></html>') == '2020-05-05'
    assert find_date('<html><body><p><em>Son güncelleme: 5/5/20</em></p></body></html>') == '2020-05-05'
    assert find_date('<html><body><p><em>Son güncellenme: 5/5/2020</em></p></body></html>') == '2020-05-05'
    assert find_date('<html><body><p><em>Yayımlama tarihi: 05.05.2020</em></p></body></html>') == '2020-05-05'
    assert find_date('<html><body><p><em>Son güncelleme tarihi: 5/5/20</em></p></body></html>') == '2020-05-05'
    assert find_date('<html><body><p><em>5/5/20 tarihinde güncellendi.</em></p></body></html>') == '2020-05-05'
    assert find_date('''<html><body><p><em>5/5/20'de güncellendi.</em></p></body></html>''') == '2020-05-05'
    assert find_date('<html><body><p><em>5/5/2020 tarihinde yayımlandı.</em></p></body></html>') == '2020-05-05'
    assert find_date('<html><body><p><em>05.05.2020 tarihinde yayınlandı.</em></p></body></html>') == '2020-05-05'


def test_parser():
    '''test argument parsing for the command-line interface'''
    testargs = ['-f', '-v', '--original', '-max', '2015-12-31', '-u', 'https://www.example.org']
    with patch.object(sys, 'argv', testargs):
        args = parse_args(testargs)
    assert args.fast is True
    assert args.original is True
    assert args.verbose is True
    assert args.maxdate == '2015-12-31'
    assert args.URL == 'https://www.example.org'
    testargs = ['-f', '-min', '2015-12-31']
    with patch.object(sys, 'argv', testargs):
        args = parse_args(testargs)
    assert args.fast is True
    assert args.original is False
    assert args.verbose is False
    assert args.mindate == '2015-12-31'
    # version
    f = io.StringIO()
    testargs = ['', '--version']
    with pytest.raises(SystemExit) as e, redirect_stdout(f):
        with patch.object(sys, 'argv', testargs):
            args = parse_args(testargs)
    assert e.type == SystemExit and e.value.code == 0
    assert re.match(r'Htmldate [0-9]\.[0-9]+\.[0-9] - Python [0-9]\.[0-9]+\.[0-9]', f.getvalue())


def test_cli():
    '''test the command-line interface'''
    assert examine(' ', extensive_bool=True) is None
    assert examine('0'*int(10e7), extensive_bool=True) is None
    assert examine(' ', False) is None
    assert examine('0'*int(10e7), False) is None
    assert examine('<?xml version="1.0" encoding="utf-8"?><!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/><meta http-equiv="Content-Type" content="text/html; charset=utf-8"/></head><body><p>A</p><p>B</p></body></html>') is None
    assert examine('<html><body><span class="entry-date">12. Juli 2016</span></body></html>', True) == '2016-07-12'
    assert examine('<html><body>2016-07-12</body></html>', extensive_bool=True) == '2016-07-12'
    assert examine('<html><body>2016-07-12</body></html>', extensive_bool=True, maxdate='2015-01-01') is None
    assert examine('<html><body>2016-07-12</body></html>', extensive_bool=True, maxdate='2017-12-31') == '2016-07-12'
    assert examine('<html><body>2016-07-12</body></html>', extensive_bool=True, maxdate='2017-41-41') == '2016-07-12'
    # first test
    testargs = ['', '-u', '123']
    with patch.object(sys, 'argv', testargs):
        args = parse_args(testargs)
    with pytest.raises(SystemExit) as err:
        process_args(args)
    assert err.type == SystemExit
    # meaningful test
    testargs = ['', '-u', 'https://httpbin.org/html']
    with patch.object(sys, 'argv', testargs):
        args = parse_args(testargs)
    f = io.StringIO()
    with redirect_stdout(f):
        process_args(args)
    assert len(f.getvalue()) == 0
    # second test
    args.URL = None
    args.inputfile = os.path.join(TEST_DIR, 'testlist.txt')
    f = io.StringIO()
    with redirect_stdout(f):
        process_args(args)
    assert f.getvalue() == 'https://httpbin.org/html\tNone\n'
    # third test: Linux and MacOS only
    if os.name != 'nt':
        args.inputfile = None
        sys.stdin = open(os.path.join(TEST_DIR, 'cache', 'befifty.montauk.html'), 'r')
        f = io.StringIO()
        with redirect_stdout(f):
            process_args(args)
        assert f.getvalue() == '2017-07-12\n'
        sys.stdin = sys.__stdin__


def test_download():
    '''test page download'''
    with pytest.raises(SystemExit):
        with patch.object(sys, 'argv', ['', '-u', 'https://httpbin.org/status/404']):
            main()
    url = 'https://httpbin.org/status/200'
    teststring = fetch_url(url)
    assert teststring is None
    assert examine(teststring) is None
    url = 'https://httpbin.org/links/2/2'
    teststring = fetch_url(url)
    assert teststring is not None
    assert examine(teststring) is None
    url = 'https://httpbin.org/html'
    teststring = fetch_url(url)
    assert teststring is not None
    assert examine(teststring, False) is None


def test_readme_examples():
    '''Test README example for consistency'''
    with pytest.raises(ValueError):
        find_date('http://')
    with pytest.raises(ValueError):
        find_date('https://httpbin.org/status/404')
    assert find_date(load_mock_page('http://blog.python.org/2016/12/python-360-is-now-available.html')) == '2016-12-23'
    assert find_date(load_mock_page('https://creativecommons.org/about/'), extensive_search=False) is None
    htmldoc = '<html><body><span class="entry-date">July 12th, 2016</span></body></html>'
    assert find_date(htmldoc) == '2016-07-12'
    mytree = html.fromstring('<html><body><span class="entry-date">July 12th, 2016</span></body></html>')
    assert find_date(mytree) == '2016-07-12'
    #print(find_date(load_mock_page('https://www.gnu.org/licenses/gpl-3.0.en.html'), outputformat='%d %B %Y', original_date=True)) # could also be: 29 June 2007
    assert find_date(load_mock_page('https://www.gnu.org/licenses/gpl-3.0.en.html'), outputformat='%d %B %Y') == '18 November 2016'
    #print(find_date(load_mock_page('https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/'), original_date=False))
    #assert find_date(load_mock_page('https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/')) == '2019-06-24'
    assert find_date(load_mock_page('https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/'), original_date=True) == '2016-06-23'
    assert find_date('https://example.org/') is None
    assert find_date(load_mock_page('https://blog.wikimedia.org/2018/06/28/interactive-maps-now-in-your-language/')) == '2018-06-28'


def test_dependencies():
    '''Test README example for consistency'''
    if EXT_PARSER is True:
        assert try_ymd_date('Fri | September 1 | 2017', OUTPUTFORMAT, True, MIN_DATE, LATEST_POSSIBLE) == '2017-09-01'
        assert find_date(load_mock_page('https://blogs.mediapart.fr/elba/blog/260619/violences-policieres-bombe-retardement-mediatique'), original_date=True) == '2019-06-27'
        assert find_date(load_mock_page('https://la-bas.org/la-bas-magazine/chroniques/Didier-Porte-souhaite-la-Sante-a-Balkany')) == '2019-06-28'
        assert find_date(load_mock_page('https://www.revolutionpermanente.fr/Antonin-Bernanos-en-prison-depuis-pres-de-deux-mois-en-raison-de-son-militantisme')) == '2019-06-13'



if __name__ == '__main__':

    # meta
    test_readme_examples()

    # function-level
    test_input()
    test_sanity()
    test_date_validator()
    test_search_pattern()
    test_try_ymd_date()
    test_convert_date()
    test_compare_reference()
    test_candidate_selection()
    test_regex_parse()
    test_external_date_parser()
    # test_header()

    # module-level
    test_no_date()
    test_exact_date()
    test_approximate_date()
    test_search_html()
    test_url()
    test_approximate_url()
    test_idiosyncrasies()
    # new_pages()

    # dependencies
    test_dependencies()

    # cli
    test_parser()
    test_cli()

    # loading functions
    test_download()

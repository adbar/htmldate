# pylint:disable-msg=W1401
"""
Real-world tests for the htmldate library.
"""

import datetime
import io
import logging
import os
import sys

from contextlib import redirect_stdout
from unittest.mock import patch

import pytest

try:
    import dateparser

    EXT_PARSER = True
    PARSER = dateparser.DateDataParser(
        languages=["de", "en"],
        settings={
            "PREFER_DAY_OF_MONTH": "first",
            "PREFER_DATES_FROM": "past",
            "DATE_ORDER": "DMY",
        },
    )  # allow_redetect_language=False,
except ImportError:
    EXT_PARSER = False

from lxml import html

from htmldate.cli import parse_args, process_args
from htmldate.core import find_date, search_page
from htmldate.settings import MIN_DATE
from htmldate.utils import detect_encoding


TEST_DIR = os.path.abspath(os.path.dirname(__file__))
OUTPUTFORMAT = "%Y-%m-%d"

LATEST_POSSIBLE = datetime.datetime.now()

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

MOCK_PAGES = {
    "http://blog.kinra.de/?p=959/": "kinra.de.html",
    "http://blog.python.org/2016/12/python-360-is-now-available.html": "blog.python.org.html",
    "http://blog.todamax.net/2018/midp-emulator-kemulator-und-brick-challenge/": "blog.todamax.net.html",
    "http://carta.info/der-neue-trend-muss-statt-wunschkoalition/": "carta.info.html",
    "https://500px.com/photo/26034451/spring-in-china-by-alexey-kruglov": "500px.com.spring.html",
    "https://bayern.de/": "bayern.de.html",
    "https://creativecommons.org/about/": "creativecommons.org.html",
    "https://die-partei.net/sh/": "die-partei.net.sh.html",
    "https://en.blog.wordpress.com/": "blog.wordpress.com.html",
    "https://en.support.wordpress.com/": "support.wordpress.com.html",
    "https://futurezone.at/digital-life/wie-creativecommons-richtig-genutzt-wird/24.600.504": "futurezone.at.cc.html",
    "https://github.com/adbar/htmldate": "github.com.html",
    "https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/": "netzpolitik.org.abmahnungen.html",
    "https://pixabay.com/en/service/terms/": "pixabay.com.tos.html",
    "https://www.austria.info/": "austria.info.html",
    "https://www.befifty.de/home/2017/7/12/unter-uns-montauk": "befifty.montauk.html",
    "https://www.beltz.de/fachmedien/paedagogik/didacta_2019_in_koeln_19_23_februar/beltz_veranstaltungen_didacta_2016/veranstaltung.html?tx_news_pi1%5Bnews%5D=14392&tx_news_pi1%5Bcontroller%5D=News&tx_news_pi1%5Baction%5D=detail&cHash=10b1a32fb5b2b05360bdac257b01c8fa": "beltz.de.didakta.html",
    "https://www.channelpartner.de/a/sieben-berufe-die-zukunft-haben,3050673": "channelpartner.de.berufe.html",
    "https://www.creativecommons.at/faircoin-hackathon": "creativecommons.at.faircoin.html",
    "https://www.deutschland.de/en": "deutschland.de.en.html",
    "https://www.eff.org/files/annual-report/2015/index.html": "eff.org.2015.html",
    "https://www.facebook.com/visitaustria/": "facebook.com.visitaustria.html",
    "https://www.gnu.org/licenses/gpl-3.0.en.html": "gnu.org.gpl.html",
    "https://www.goodform.ch/blog/schattiges_plaetzchen": "goodform.ch.blog.html",
    "https://www.horizont.net/marketing/kommentare/influencer-marketing-was-sich-nach-dem-vreni-frost-urteil-aendert-und-aendern-muss-172529": "horizont.net.html",
    "https://www.intel.com/content/www/us/en/legal/terms-of-use.html": "intel.com.tos.html",
    "https://www.pferde-fuer-unsere-kinder.de/unsere-projekte/": "pferde.projekte.de.html",
    "https://www.rosneft.com/business/Upstream/Licensing/": "rosneft.com.licensing.html",
    "https://www.scs78.de/news/items/warm-war-es-schoen-war-es.html": "scs78.de.html",
    "https://www.tagesausblick.de/Analyse/USA/DOW-Jones-Jahresendrally-ade__601.html": "tagesausblick.de.dow.html",
    "https://www.transgen.de/aktuell/2687.afrikanische-schweinepest-genome-editing.html": "transgen.de.aktuell.html",
    "https://www.weltwoche.ch/ausgaben/2019-4/artikel/forbes-die-weltwoche-ausgabe-4-2019.html": "weltwoche.ch.html",
    "https://www.wunderweib.de/manuela-reimann-hochzeitsueberraschung-in-bayern-107930.html": "wunderweib.html",
    "http://unexpecteduser.blogspot.de/2011/": "unexpecteduser.2011.html",
    "http://viehbacher.com/de/spezialisierung/internationale-forderungsbeitreibung": "viehbacher.com.forderungsbetreibung.html",
    "http://www.eza.gv.at/das-ministerium/presse/aussendungen/2018/07/aussenministerin-karin-kneissl-beim-treffen-der-deutschsprachigen-aussenminister-in-luxemburg/": "eza.gv.at.html",
    "http://www.freundeskreis-videoclips.de/waehlen-sie-car-player-tipps-zur-auswahl-der-besten-car-cd-player/": "freundeskreis-videoclips.de.html",
    "http://www.greenpeace.org/international/en/campaigns/forests/asia-pacific/": "greenpeace.org.forests.html",
    "http://www.heimicke.de/chronik/zahlen-und-daten/": "heimicke.de.zahlen.html",
    "http://www.hobby-werkstatt-blog.de/arduino/424-eine-arduino-virtual-wall-fuer-den-irobot-roomba.php": "hobby-werkstatt-blog.de.roomba.html",
    "http://www.hundeverein-kreisunna.de/termine.html": "hundeverein-kreisunna.de.html",
    "http://www.hundeverein-querfurt.de/index.php?option=com_content&view=article&id=54&Itemid=50": "hundeverein-querfurt.de.html",
    "http://www.jovelstefan.de/2012/05/11/parken-in-paris/": "jovelstefan.de.parken.html",
    "http://www.klimawandel-global.de/klimaschutz/energie-sparen/elektromobilitat-der-neue-trend/": "klimawandel-global.de.html",
    "http://www.medef.com/en/content/alternative-dispute-resolution-for-antitrust-damages": "medef.fr.dispute.html",
    "http://www.pbrunst.de/news/2011/12/kein-cyberterrorismus-diesmal/": "pbrunst.de.html",
    "http://www.stuttgart.de/": "stuttgart.de.html",
    "https://paris-luttes.info/quand-on-comprend-que-les-grenades-12355": "paris-luttes.info.html",
    "https://www.brigitte.de/aktuell/riverdale--so-ehrt-die-serie-luke-perry-in-staffel-vier-11602344.html": "brigitte.de.riverdale.html",
    "https://www.ldt.de/ldtblog/fall-in-love-with-black/": "ldt.de.fallinlove.html",
    "http://www.loldf.org/spip.php?article717": "loldf.org.html",
    "https://www.beltz.de/sachbuch_ratgeber/buecher/produkt_produktdetails/37219-12_wege_zu_guter_pflege.html": "beltz.de.12wege.html",
    "https://www.oberstdorf-resort.de/interaktiv/blog/unser-kraeutergarten-wannenkopfhuette.html": "oberstdorfresort.de.kraeuter.html",
    "https://www.wienbadminton.at/news/119843/Come-Together": "wienbadminton.at.html",
    "https://blog.wikimedia.org/2018/06/28/interactive-maps-now-in-your-language/": "blog.wikimedia.interactivemaps.html",
    "https://blogs.mediapart.fr/elba/blog/260619/violences-policieres-bombe-retardement-mediatique": "mediapart.fr.violences.html",
    "https://verfassungsblog.de/the-first-decade/": "verfassungsblog.de.decade.html",
    "https://cric-grenoble.info/infos-locales/article/putsh-en-cours-a-radio-kaleidoscope-1145": "cric-grenoble.info.radio.html",
    "https://www.sebastian-kurz.at/magazin/wasserstoff-als-schluesseltechnologie": "kurz.at.wasserstoff.html",
    "https://la-bas.org/la-bas-magazine/chroniques/Didier-Porte-souhaite-la-Sante-a-Balkany": "la-bas.org.porte.html",
    "https://exporo.de/wiki/europaeische-zentralbank-ezb/": "exporo.de.ezb.html",
    "https://www.revolutionpermanente.fr/Antonin-Bernanos-en-prison-depuis-pres-de-deux-mois-en-raison-de-son-militantisme": "revolutionpermanente.fr.antonin.html",
    "http://www.wara-enforcement.org/guinee-un-braconnier-delephant-interpelle-et-condamne-a-la-peine-maximale/": "wara-enforcement.org.guinee.html",
    "https://ebene11.com/die-arbeit-mit-fremden-dwg-dateien-in-autocad": "ebene11.com.autocad.html",
    "https://www.acredis.com/schoenheitsoperationen/augenlidstraffung/": "acredis.com.augenlidstraffung.html",
    "https://www.hertie-school.org/en/debate/detail/content/whats-on-the-cards-for-von-der-leyen/": "hertie-school.org.leyen.html",
    "https://www.adac.de/rund-ums-fahrzeug/tests/kindersicherheit/kindersitztest-2018/": "adac.de.kindersitztest.html",
    "http://web.archive.org/web/20210916140120/https://www.kath.ch/die-insel-der-klosterzoeglinge/": "archive.org.kath.ch.html",
}

MEDIACLOUD_PAGES = {"pagename": "thing.html"}


def load_mock_page(url, dirname="cache", dictname=MOCK_PAGES):
    """load mock page from samples"""
    with open(os.path.join(TEST_DIR, dirname, dictname[url]), "rb") as inputf:
        return inputf.read()


def load_mediacloud_page(url):
    """load mediacloud page from samples"""
    return load_mock_page(url, dirname="test_set", dictname=MEDIACLOUD_PAGES)


def test_no_date():
    "These pages should not return any date"
    assert (
        find_date(
            load_mock_page(
                "https://www.intel.com/content/www/us/en/legal/terms-of-use.html"
            )
        )
        is None
    )
    # safe search
    assert (
        find_date(
            load_mock_page("https://en.support.wordpress.com/"), extensive_search=False
        )
        is None
    )
    ## assert find_date(load_mock_page("https://en.support.wordpress.com/")) is None


def test_exact_date():
    "These pages should return an exact date"

    ## link in header
    assert (
        find_date(
            load_mock_page("http://www.jovelstefan.de/2012/05/11/parken-in-paris/")
        )
        == "2012-05-11"
    )

    ## meta in header
    assert (
        find_date(
            load_mock_page(
                "https://500px.com/photo/26034451/spring-in-china-by-alexey-kruglov"
            )
        )
        == "2013-02-16"
    )

    ## time in document body
    assert (
        find_date(
            load_mock_page("https://www.facebook.com/visitaustria/"), original_date=True
        )
        == "2017-10-06"
    )
    assert (
        find_date(
            load_mock_page("https://www.facebook.com/visitaustria/"),
            original_date=False,
        )
        == "2017-10-08"
    )
    assert (
        find_date(
            load_mock_page(
                "http://www.medef.com/en/content/alternative-dispute-resolution-for-antitrust-damages"
            )
        )
        == "2017-09-01"
    )

    ## precise pattern in document body
    assert (
        find_date(
            load_mock_page(
                "https://www.tagesausblick.de/Analyse/USA/DOW-Jones-Jahresendrally-ade__601.html"
            )
        )
        == "2012-12-22"
    )
    assert (
        find_date(
            load_mock_page(
                "http://blog.todamax.net/2018/midp-emulator-kemulator-und-brick-challenge/"
            )
        )
        == "2018-02-15"
    )
    # JSON datePublished
    assert (
        find_date(
            load_mock_page(
                "https://www.acredis.com/schoenheitsoperationen/augenlidstraffung/"
            ),
            original_date=True,
        )
        == "2018-02-28"
    )
    # JSON dateModified
    assert (
        find_date(
            load_mock_page(
                "https://www.channelpartner.de/a/sieben-berufe-die-zukunft-haben,3050673"
            ),
            original_date=False,
        )
        == "2019-04-03"
    )

    ## meta in document body
    assert (
        find_date(
            load_mock_page(
                "https://futurezone.at/digital-life/wie-creativecommons-richtig-genutzt-wird/24.600.504"
            ),
            original_date=True,
        )
        == "2013-08-09"
    )
    assert (
        find_date(
            load_mock_page(
                "https://www.horizont.net/marketing/kommentare/influencer-marketing-was-sich-nach-dem-vreni-frost-urteil-aendert-und-aendern-muss-172529"
            )
        )
        == "2019-01-29"
    )
    assert (
        find_date(
            load_mock_page(
                "http://www.klimawandel-global.de/klimaschutz/energie-sparen/elektromobilitat-der-neue-trend/"
            )
        )
        == "2013-05-03"
    )
    assert (
        find_date(
            load_mock_page(
                "http://www.hobby-werkstatt-blog.de/arduino/424-eine-arduino-virtual-wall-fuer-den-irobot-roomba.php"
            )
        )
        == "2015-12-14"
    )
    assert (
        find_date(
            load_mock_page(
                "https://www.beltz.de/fachmedien/paedagogik/didacta_2019_in_koeln_19_23_februar/beltz_veranstaltungen_didacta_2016/veranstaltung.html?tx_news_pi1%5Bnews%5D=14392&tx_news_pi1%5Bcontroller%5D=News&tx_news_pi1%5Baction%5D=detail&cHash=10b1a32fb5b2b05360bdac257b01c8fa"
            )
        )
        == "2019-02-20"
    )
    assert (
        find_date(
            load_mock_page("https://www.wienbadminton.at/news/119843/Come-Together"),
            extensive_search=False,
        )
        is None
    )
    assert (
        find_date(
            load_mock_page("https://www.wienbadminton.at/news/119843/Come-Together"),
            extensive_search=True,
        )
        == "2018-05-06"
    )

    # abbr in document body
    assert find_date(load_mock_page("http://blog.kinra.de/?p=959/")) == "2012-12-16"

    # time in document body
    assert (
        find_date(
            load_mock_page(
                "https://www.adac.de/rund-ums-fahrzeug/tests/kindersicherheit/kindersitztest-2018/"
            )
        )
        == "2018-10-23"
    )

    ## other expressions in document body
    assert find_date(load_mock_page("http://www.stuttgart.de/")) == "2017-10-09"
    ## in document body
    assert (
        find_date(
            load_mock_page("https://github.com/adbar/htmldate"), original_date=False
        )
        == "2017-11-28"
    )  # was '2019-01-01'
    assert (
        find_date(
            load_mock_page("https://github.com/adbar/htmldate"), original_date=True
        )
        == "2016-07-12"
    )

    assert find_date(load_mock_page("https://en.blog.wordpress.com/")) == "2017-08-30"
    assert find_date(load_mock_page("https://www.austria.info/")) == "2017-09-07"
    assert (
        find_date(
            load_mock_page("https://www.eff.org/files/annual-report/2015/index.html")
        )
        == "2016-05-04"
    )
    assert (
        find_date(load_mock_page("http://unexpecteduser.blogspot.de/2011/"))
        == "2011-03-30"
    )
    assert find_date(load_mock_page("https://die-partei.net/sh/")) == "2014-07-19"
    assert (
        find_date(
            load_mock_page("https://www.rosneft.com/business/Upstream/Licensing/")
        )
        == "2017-02-27"
    )  # most probably 2014-12-31, found in text
    assert (
        find_date(
            load_mock_page(
                "http://www.freundeskreis-videoclips.de/waehlen-sie-car-player-tipps-zur-auswahl-der-besten-car-cd-player/"
            )
        )
        == "2017-07-12"
    )
    assert (
        find_date(
            load_mock_page(
                "https://www.scs78.de/news/items/warm-war-es-schoen-war-es.html"
            )
        )
        == "2018-06-10"
    )
    assert (
        find_date(load_mock_page("https://www.goodform.ch/blog/schattiges_plaetzchen"))
        == "2018-06-27"
    )
    assert (
        find_date(
            load_mock_page(
                "https://www.transgen.de/aktuell/2687.afrikanische-schweinepest-genome-editing.html"
            )
        )
        == "2018-01-18"
    )
    assert (
        find_date(
            load_mock_page(
                "http://www.eza.gv.at/das-ministerium/presse/aussendungen/2018/07/aussenministerin-karin-kneissl-beim-treffen-der-deutschsprachigen-aussenminister-in-luxemburg/"
            )
        )
        == "2018-07-03"
    )
    assert (
        find_date(
            load_mock_page(
                "https://www.weltwoche.ch/ausgaben/2019-4/artikel/forbes-die-weltwoche-ausgabe-4-2019.html"
            )
        )
        == "2019-01-23"
    )

    # other format
    assert (
        find_date(
            load_mock_page("http://unexpecteduser.blogspot.de/2011/"),
            outputformat="%d %B %Y",
        )
        == "30 March 2011"
    )
    assert (
        find_date(
            load_mock_page(
                "http://blog.python.org/2016/12/python-360-is-now-available.html"
            ),
            outputformat="%d %B %Y",
        )
        == "23 December 2016"
    )

    # additional list
    assert (
        find_date(
            load_mock_page(
                "http://carta.info/der-neue-trend-muss-statt-wunschkoalition/"
            )
        )
        == "2012-05-08"
    )
    assert (
        find_date(
            load_mock_page(
                "https://www.wunderweib.de/manuela-reimann-hochzeitsueberraschung-in-bayern-107930.html"
            )
        )
        == "2019-06-20"
    )
    assert (
        find_date(
            load_mock_page("https://www.befifty.de/home/2017/7/12/unter-uns-montauk")
        )
        == "2017-07-12"
    )
    assert (
        find_date(
            load_mock_page(
                "https://www.brigitte.de/aktuell/riverdale--so-ehrt-die-serie-luke-perry-in-staffel-vier-11602344.html"
            )
        )
        == "2019-06-20"
    )  # returns an error
    assert (
        find_date(load_mock_page("http://www.loldf.org/spip.php?article717"))
        == "2019-06-27"
    )
    assert (
        find_date(
            load_mock_page(
                "https://www.beltz.de/sachbuch_ratgeber/buecher/produkt_produktdetails/37219-12_wege_zu_guter_pflege.html"
            )
        )
        == "2019-02-07"
    )
    assert (
        find_date(
            load_mock_page(
                "https://www.oberstdorf-resort.de/interaktiv/blog/unser-kraeutergarten-wannenkopfhuette.html"
            )
        )
        == "2018-06-20"
    )
    assert (
        find_date(
            load_mock_page("https://www.wienbadminton.at/news/119843/Come-Together")
        )
        == "2018-05-06"
    )
    assert (
        find_date(load_mock_page("https://www.ldt.de/ldtblog/fall-in-love-with-black/"))
        == "2017-08-08"
    )
    assert (
        find_date(
            load_mock_page(
                "https://paris-luttes.info/quand-on-comprend-que-les-grenades-12355"
            ),
            original_date=True,
        )
        == "2019-06-29"
    )
    assert (
        find_date(load_mock_page("https://verfassungsblog.de/the-first-decade/"))
        == "2019-07-13"
    )
    assert (
        find_date(
            load_mock_page(
                "https://cric-grenoble.info/infos-locales/article/putsh-en-cours-a-radio-kaleidoscope-1145"
            )
        )
        == "2019-06-09"
    )
    assert (
        find_date(
            load_mock_page(
                "https://www.sebastian-kurz.at/magazin/wasserstoff-als-schluesseltechnologie"
            )
        )
        == "2019-07-30"
    )
    assert (
        find_date(
            load_mock_page("https://exporo.de/wiki/europaeische-zentralbank-ezb/")
        )
        == "2018-01-01"
    )
    # only found by extensive search
    assert (
        find_date(
            load_mock_page(
                "https://ebene11.com/die-arbeit-mit-fremden-dwg-dateien-in-autocad"
            ),
            extensive_search=False,
        )
    ) is None
    assert (
        find_date(
            load_mock_page(
                "https://ebene11.com/die-arbeit-mit-fremden-dwg-dateien-in-autocad"
            ),
            extensive_search=True,
        )
    ) == "2017-01-12"
    assert (
        find_date(
            load_mock_page(
                "https://www.hertie-school.org/en/debate/detail/content/whats-on-the-cards-for-von-der-leyen/"
            ),
            extensive_search=False,
        )
    ) is None
    assert (
        find_date(
            load_mock_page(
                "https://www.hertie-school.org/en/debate/detail/content/whats-on-the-cards-for-von-der-leyen/"
            ),
            extensive_search=True,
        )
    ) == "2019-12-02"  # 2019-02-12?

    # date not in footer but at the start of the article
    assert (
        find_date(
            load_mock_page(
                "http://www.wara-enforcement.org/guinee-un-braconnier-delephant-interpelle-et-condamne-a-la-peine-maximale/"
            )
        )
        == "2016-09-27"
    )

    # archive.org documents
    assert (
        find_date(
            load_mock_page(
                "http://web.archive.org/web/20210916140120/https://www.kath.ch/die-insel-der-klosterzoeglinge/"
            ),
            extensive_search=False,
        )
        is None
    )
    assert (
        find_date(
            load_mock_page(
                "http://web.archive.org/web/20210916140120/https://www.kath.ch/die-insel-der-klosterzoeglinge/"
            ),
            extensive_search=True,
        )
        == "2021-07-13"
    )


def test_approximate_date():
    "These pages should return an approximate date"
    # copyright text
    assert (
        find_date(
            load_mock_page(
                "http://viehbacher.com/de/spezialisierung/internationale-forderungsbeitreibung"
            )
        )
        == "2016-01-01"
    )  # somewhere in 2016
    # other
    assert (
        find_date(
            load_mock_page("https://creativecommons.org/about/"), original_date=False
        )
        == "2017-08-11"
    )  # or '2017-08-03'
    assert (
        find_date(
            load_mock_page("https://creativecommons.org/about/"), original_date=True
        )
        == "2016-05-22"
    )  # or '2017-08-03'
    assert find_date(load_mock_page("https://www.deutschland.de/en")) == "2017-08-01"
    assert (
        find_date(
            load_mock_page(
                "http://www.greenpeace.org/international/en/campaigns/forests/asia-pacific/"
            )
        )
        == "2017-04-28"
    )
    assert (
        find_date(load_mock_page("https://www.creativecommons.at/faircoin-hackathon"))
        == "2017-07-24"
    )
    assert (
        find_date(load_mock_page("https://pixabay.com/en/service/terms/"))
        == "2017-08-09"
    )
    assert (
        find_date(
            load_mock_page("https://bayern.de/"),
        )
        == "2017-10-06"
    )
    assert (
        find_date(
            load_mock_page("https://www.pferde-fuer-unsere-kinder.de/unsere-projekte/")
        )
        == "2016-07-20"
    )  # most probably 2016-07-15
    # LXML bug filed: https://bugs.launchpad.net/lxml/+bug/1955915
    assert (
        find_date(
            load_mock_page(
                "http://www.hundeverein-querfurt.de/index.php?option=com_content&view=article&id=54&Itemid=50"
            ),
            original_date=False,
        )
        == "2016-12-04"
    )  # 2010-11-01 in meta, 2016 more plausible
    assert (
        find_date(
            load_mock_page(
                "http://www.pbrunst.de/news/2011/12/kein-cyberterrorismus-diesmal/"
            ),
            original_date=False,
        )
        == "2011-12-01"
    )
    ## TODO: problem, take URL instead
    assert (
        find_date(
            load_mock_page(
                "http://www.pbrunst.de/news/2011/12/kein-cyberterrorismus-diesmal/"
            ),
            original_date=True,
        )
        == "2010-06-01"
    )
    # dates in table
    assert (
        find_date(load_mock_page("http://www.hundeverein-kreisunna.de/termine.html"))
        == "2017-03-29"
    )  # probably newer


def test_search_html(original_date=False, min_date=MIN_DATE, max_date=LATEST_POSSIBLE):
    "Test the pattern search in raw HTML"
    # file input + output format
    fileinput = load_mock_page("http://www.heimicke.de/chronik/zahlen-und-daten/")
    encoding = detect_encoding(fileinput)[0]
    assert (
        search_page(
            fileinput.decode(encoding), "%d %B %Y", original_date, min_date, max_date
        )
        == "06 April 2019"
    )


def test_readme_examples():
    "Test README examples for consistency"
    with pytest.raises(ValueError):
        find_date("http://")
    with pytest.raises(ValueError):
        find_date("https://httpbin.org/status/404")
    assert (
        find_date(
            load_mock_page(
                "http://blog.python.org/2016/12/python-360-is-now-available.html"
            )
        )
        == "2016-12-23"
    )
    assert (
        find_date(
            load_mock_page("https://creativecommons.org/about/"), extensive_search=False
        )
        is None
    )
    htmldoc = (
        '<html><body><span class="entry-date">July 12th, 2016</span></body></html>'
    )
    assert find_date(htmldoc) == "2016-07-12"
    mytree = html.fromstring(
        '<html><body><span class="entry-date">July 12th, 2016</span></body></html>'
    )
    assert find_date(mytree) == "2016-07-12"
    assert (
        find_date(
            load_mock_page("https://www.gnu.org/licenses/gpl-3.0.en.html"),
            outputformat="%d %B %Y",
        )
        == "18 November 2016"
    )  # could also be: 29 June 2007
    assert (
        find_date(
            load_mock_page(
                "https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/"
            ),
            original_date=False,
        )
        == "2016-06-23"
    )  # was '2019-06-24'
    assert (
        find_date(
            load_mock_page(
                "https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/"
            ),
            original_date=True,
        )
        == "2016-06-23"
    )
    assert find_date("https://example.org/") is None
    assert (
        find_date(
            load_mock_page(
                "https://blog.wikimedia.org/2018/06/28/interactive-maps-now-in-your-language/"
            )
        )
        == "2018-06-28"
    )
    precise_date_html = """
        <!doctype html> <html lang="en-CA" class="no-js"> <head> <link rel="canonical" href="https://www.fool.ca/2022/10/20/3-stable-stocks-id-buy-if-the-market-tanks-further/"/> <meta property="article:published_time" content="2022-10-20T18:45:00+00:00"/><meta property="article:modified_time" content="2022-10-20T18:35:08+00:00"/> <script type="application/ld+json" class="yoast-schema-graph">{"@context":"https://schema.org","@graph":[{"@type":"WebPage","@id":"https://www.fool.ca/2022/10/20/3-stable-stocks-id-buy-if-the-market-tanks-further/#webpage","url":"https://www.fool.ca/2022/10/20/3-stable-stocks-id-buy-if-the-market-tanks-further/","name":"3 Stable Stocks I'd Buy if the Market Tanks Further | The Motley Fool Canada","isPartOf":{"@id":"https://www.fool.ca/#website"},"datePublished":"2022-10-20T18:45:00+00:00","dateModified":"2022-10-20T18:35:08+00:00","description":"Dividend aristocrats contain stable stocks that any investor should consider, but these three offer the best chance at future growth as well.","breadcrumb":{"@id":"https://www.fool.ca/2022/10/20/3-stable-stocks-id-buy-if-the-market-tanks-further/#breadcrumb"},"inLanguage":"en-CA"},{"@type":"NewsArticle","@id":"https://www.fool.ca/2022/10/20/3-stable-stocks-id-buy-if-the-market-tanks-further/#article","isPartOf":{"@id":"https://www.fool.ca/2022/10/20/3-stable-stocks-id-buy-if-the-market-tanks-further/#webpage"},"author":{"@id":"https://www.fool.ca/#/schema/person/e0d452bd1e82135f310295e7dc650aca"},"headline":"3 Stable Stocks I&#8217;d Buy if the Market Tanks Further","datePublished":"2022-10-20T18:45:00+00:00","dateModified":"2022-10-20T18:35:08+00:00"}]}</script> </head> <body class="post-template-default single single-post postid-1378278 single-format-standard mega-menu-main-menu-2020 mega-menu-footer-2020" data-has-main-nav="true"> <span class="posted-on">Published <time class="entry-date published" datetime="2022-10-20T14:45:00-04:00">October 20, 2:45 pm EDT</time></span> </body> </html>
    """
    assert (
        find_date(
            precise_date_html,
            outputformat="%Y-%m-%dT%H:%M:%S%z",
            original_date=True,
            deferred_url_extractor=True,
        )
        == "2022-10-20T18:45:00+0000"
    )
    assert (
        find_date(
            precise_date_html, outputformat="%Y-%m-%dT%H:%M:%S%z", original_date=True
        )
        == "2022-10-20T00:00:00"
    )


def test_dependencies():
    "Test README examples for consistency"
    if EXT_PARSER is True:
        assert (
            find_date(
                load_mock_page(
                    "https://blogs.mediapart.fr/elba/blog/260619/violences-policieres-bombe-retardement-mediatique"
                ),
                original_date=True,
            )
            == "2019-06-27"
        )
        assert (
            find_date(
                load_mock_page(
                    "https://la-bas.org/la-bas-magazine/chroniques/Didier-Porte-souhaite-la-Sante-a-Balkany"
                )
            )
            == "2019-06-28"
        )
        assert (
            find_date(
                load_mock_page(
                    "https://www.revolutionpermanente.fr/Antonin-Bernanos-en-prison-depuis-pres-de-deux-mois-en-raison-de-son-militantisme"
                )
            )
            == "2019-06-13"
        )


def test_cli():
    "Test the command-line interface"
    # third test: Linux and MacOS only
    if os.name != "nt":
        testargs = [""]
        with patch.object(sys, "argv", testargs):
            args = parse_args(testargs)
        sys.stdin = open(
            os.path.join(TEST_DIR, "cache", "befifty.montauk.html"),
            "r",
            encoding="utf-8",
        )
        f = io.StringIO()
        with redirect_stdout(f):
            process_args(args)
        assert f.getvalue() == "2017-07-12\n"
        sys.stdin = sys.__stdin__


if __name__ == "__main__":
    # meta
    test_readme_examples()
    test_dependencies()

    # module-level
    test_no_date()
    test_exact_date()
    test_approximate_date()
    test_search_html()
    test_cli()

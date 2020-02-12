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

from articleDateExtractor import extractArticlePublishedDate
from date_guesser import guess_date, Accuracy
from goose3 import Goose
from htmldate import find_date
from htmldate.validators import convert_date
from newspaper import Article
from newspaper.article import ArticleDownloadState
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
'http://www.medef.com/en/content/alternative-dispute-resolution-for-antitrust-damages': {
    'file': 'medef.fr.dispute.html',
    'date': '2017-09-01',
},
'http://www.pbrunst.de/news/2011/12/kein-cyberterrorismus-diesmal/': {
    'file': 'pbrunst.de.html',
    'date': '2011-12-03',
},
'http://www.stuttgart.de/': {
    'file': 'stuttgart.de.html',
    'date': '2017-10-09',
},
'https://paris-luttes.info/quand-on-comprend-que-les-grenades-12355': {
    'file': 'paris-luttes.info.html',
    'date': '2019-06-29',
},
'https://www.brigitte.de/aktuell/riverdale--so-ehrt-die-serie-luke-perry-in-staffel-vier-11602344.html': {
    'file': 'brigitte.de.riverdale.html',
    'date': '2019-06-20',
},
'https://www.ldt.de/ldtblog/fall-in-love-with-black/': {
    'file': 'ldt.de.fallinlove.html',
    'date': '2017-08-08',
},
'http://www.loldf.org/spip.php?article717': {
    'file': 'loldf.org.html',
    'date': '2019-06-27',
},
#'https://www.beltz.de/sachbuch_ratgeber/buecher/produkt_produktdetails/37219-12_wege_zu_guter_pflege.html': {
#    'file': 'beltz.de.12wege.html',
#    'date': '',
#},
'https://www.oberstdorf-resort.de/interaktiv/blog/unser-kraeutergarten-wannenkopfhuette.html': {
    'file': 'oberstdorfresort.de.kraeuter.html',
    'date': '2018-06-20',
},
'https://www.wienbadminton.at/news/119843/Come-Together': {
    'file': 'wienbadminton.at.html',
    'date': '2018-05-06',
},
'https://blog.wikimedia.org/2018/06/28/interactive-maps-now-in-your-language/': {
    'file': 'blog.wikimedia.interactivemaps.html',
    'date': '2018-06-28',
},
'https://blogs.mediapart.fr/elba/blog/260619/violences-policieres-bombe-retardement-mediatique': {
    'file': 'mediapart.fr.violences.html',
    'date': '2019-06-27',
},
'https://verfassungsblog.de/the-first-decade/': {
    'file': 'verfassungsblog.de.decade.html',
    'date': '2019-07-13',
},
'https://cric-grenoble.info/infos-locales/article/putsh-en-cours-a-radio-kaleidoscope-1145': {
    'file': 'cric-grenoble.info.radio.html',
    'date': '2019-06-09',
},
'https://www.sebastian-kurz.at/magazin/wasserstoff-als-schluesseltechnologie': {
    'file': 'kurz.at.wasserstoff.html',
    'date': '2019-07-30',
},
'https://la-bas.org/la-bas-magazine/chroniques/Didier-Porte-souhaite-la-Sante-a-Balkany': {
    'file': 'la-bas.org.porte.html',
    'date': '2019-06-28',
},
#'https://exporo.de/wiki/europaeische-zentralbank-ezb/': {
#    'file': 'exporo.de.ezb.html',
#    'date': '',
#},
'https://www.revolutionpermanente.fr/Antonin-Bernanos-en-prison-depuis-pres-de-deux-mois-en-raison-de-son-militantisme': {
    'file': 'revolutionpermanente.fr.antonin.html',
    'date': '2019-06-13',
},
'http://www.wara-enforcement.org/guinee-un-braconnier-delephant-interpelle-et-condamne-a-la-peine-maximale/': {
    'file': 'wara-enforcement.org.guinee.html',
    'date': '2016-09-27',
},
'https://ebene11.com/die-arbeit-mit-fremden-dwg-dateien-in-autocad': {
    'file': 'ebene11.com.autocad.html',
    'date': '2017-01-12',
},
'https://www.acredis.com/schoenheitsoperationen/augenlidstraffung/': {
    'file': 'acredis.com.augenlidstraffung.html',
    'date': '2018-02-28',
},
'https://www.hertie-school.org/en/debate/detail/content/whats-on-the-cards-for-von-der-leyen/': {
    'file': 'hertie-school.org.leyen.html',
    'date': '2019-12-02',
},
'https://www.adac.de/rund-ums-fahrzeug/tests/kindersicherheit/kindersitztest-2018/': {
    'file': 'adac.de.kindersitztest.html',
    'date': '2018-10-23',
},
'https://www.ahlen.de/start/aktuelles/aktuelle/information/nachricht/aus-ahlen/reparaturcafe-am-31-januar/': {
    'file': 'ahlen.de.reparaturcafe.html',
    'date': '2020-01-27',
},
'https://rete-mirabile.net/notizen/15-jahre-rete-mirabile/': {
    'file': 'rete-mirabile.net.15jahre.html',
    'date': '2019-07-28',
},
'https://shop.nmb-media.de/eBay-Template-Datenschutz-Google-Fonts-Fontawesome': {
    'file': 'nmb-media.de.ebay.html',
    'date': '2018-06-22',
},
'https://viertausendhertz.de/ddg48/': {
    'file': 'viertausendhertz.de.ddg48.html',
    'date': '2019-12-16',
},
'http://www.bibliothek2null.de/2014/05/18/alles-neue-mach-der-mai/': {
    'file': 'bibliothek2null.de.mai.html',
    'date': '2014-05-18',
},
'http://www.helge.at/2014/03/warum-wien-zu-blod-fur-eine-staufreie-mahu-ist/': {
    'file': 'helge.at.mahu.html',
    'date': '2014-03-05',
},
'https://blogoff.de/2015/11/12/i-htm/': {
    'file': 'blogoff.de.i-htm.html',
    'date': '2015-11-12',
},
'https://de.globalvoices.org/2019/04/30/ein-jahr-voller-proteste-nicaraguaner-wollen-nicht-mehr-nur-den-rucktritt-ortegas-sondern-einen-neuanfang/': {
    'file': 'de.globalvoices.org.nicaragua.html',
    'date': '2019-04-30',
},
'http://www.heiko-adams.de/laufen-im-winter-von-baeh-zu-yeah-in-12-monaten/': {
    'file': 'heiko-adams.de.laufen.html',
    'date': '2019-02-10',
},
'https://www.faz.net/aktuell/wirtschaft/nutzerbasierte-abrechnung-musik-stars-fordern-neues-streaming-modell-16604622.html': {
    'file': 'faz.net.streaming.html',
    'date': '2020-01-28',
},
'http://wir-empfehlen.info/?p=3289': {
    'file': 'wir-empfehlen.info.3289.html',
    'date': '2020-01-03',
},
'https://nextkabinett.wordpress.com/2014/01/17/derek-jarman-%c2%b7-the-garden/': {
    'file': 'nextkabinett.wordpress.com.garden.html',
    'date': '2014-01-17',
},
'https://sprechblase.wordpress.com/2019/11/17/elektro-zapfsaeulen/': {
    'file': 'sprechblase.wordpress.com.zapfsaeulen.html',
    'date': '2019-11-17',
},
'https://creeny.wordpress.com/2020/01/24/nebelsuppe-6/': {
    'file': 'creeny.wordpress.com.nebelsuppe.html',
    'date': '2020-01-24',
},
'https://nurmeinstandpunkt.wordpress.com/2020/01/23/blogposting-01-23-2020/': {
    'file': 'nurmeinstandpunkt.wordpress.com.blogposting.html',
    'date': '2020-01-23',
},
'https://flowfx.de/blog/copy-paste-from-tmux-to-system-clipboard/': {
    'file': 'flowfx.de.tmux.html',
    'date': '2020-01-16',
},
'https://gnadlib.wordpress.com/2020/01/05/scherenschnitt-3/': {
    'file': 'gnadlib.wordpress.com.scherenschnitt.html',
    'date': '2020-01-05',
},
'https://www.spontis.de/schwarze-szene/liebe-leser-bitte-rutschen-sie-nicht-in-das-neue-jahrzehnt/': {
    'file': 'spontis.de.jahrzehnt.html',
    'date': '2019-12-31',
},
'https://www.schneems.com/2018/10/09/pair-with-me-rubocop-cop-that-detects-duplicate-array-allocations/': {
    'file': 'schneems.com.rubocop.html',
    'date': '2018-10-09',
},
'https://hackernoon.com/how-to-scrape-google-with-python-bo7d2tal': {
    'file': 'hackernoon.com.scrape.html',
    'date': '2019-12-29',
},
'www.colours-of-the-soul.alhelm.net': {
    'file': 'colours-of-the-soul.alhelm.net',
    'date': '2009-02-18',
},
'https://lernpfadprismen.wordpress.com/masse/masse-des-quaders/': {
    'file': 'lernpfadprismen.wordpress.com.masse.html',
    'date': '2015-12-07',
},
'https://grossefragen.wordpress.com/2019/03/13/wuerde-des-lebens-ein-projekt/': {
    'file': 'grossefragen.wordpress.com.projekt.html',
    'date': '2019-03-13',
},
'https://knowledge-on-air.de/2019/12/17/koa039-live-vom-knowledgecamp-2019/': {
    'file': 'knowledge-on-air.de.koa039.html',
    'date': '2019-12-17',
},
'https://campino2k.de/2016/02/28/uberspace-und-lets-encrypt/': {
    'file': 'campino2k.de.uberspace.html',
    'date': '2016-02-28',
},
'http://www.silvias.net/blog/wahlzensur-angriff-auf-universitaeten/': {
    'file': 'silvias.net.wahlzensur.html',
    'date': '2018-10-26',
},
'https://wolfsrebellen-netz.forumieren.com/t7-forums-regeln': {
    'file': 'wolfsrebellen-netz.forumieren.com.regeln.html',
    'date': '2013-10-26',
},
'https://resonator-podcast.de/2019/res158-kathrin-goebel/': {
    'file': 'resonator-podcast.de.res158.html',
    'date': '2019-08-16',
},
'https://bunterepublik.wordpress.com/2017/06/12/keine-spiel-talstrasse-zur-bunten-republik-neustadt/': {
    'file': 'bunterepublik.wordpress.com.talstrasse.html',
    'date': '2017-06-12',
},

'https://murdeltas.wordpress.com/2015/04/05/barcamp-graz-2015-politcamp-call-for-action/': {
    'file': 'murdeltas.wordpress.com.politcamp.html',
    'date': '2015-04-05',
},
'https://herrpfleger.de/2019/10/new-balance-fuelcell-echo-bringt-speed/': {
    'file': 'herrpfleger.de.fuelcell.html',
    'date': '2019-10-01',
},
'https://andreabottlinger.wordpress.com/2019/12/26/arent-we-all/': {
    'file': 'andreabottlinger.wordpress.com.arent.html',
    'date': '2019-12-26',
},
'http://www.jan-grosser.de/art/385_xum1541_dateien_zwischen_linux.html': {
    'file': 'jan-grosser.de.xum1541.html',
    'date': '2016-01-31',
},
'http://www.einfachspanien.de/malaga-die-quirlige-metropole-in-andalusien.html': {
    'file': 'einfachspanien.de.malaga.html',
    'date': '2011-11-22',
},
'https://prof-pc.de/': {
    'file': 'prof-pc.de.html',
    'date': '2017-09-10',
},
'https://mobilsicher.de/aktuelles/apple-kippt-verschluesselungsplaene-fuer-icloud': {
    'file': 'mobilsicher.de.icloud.html',
    'date': '2020-01-23',
},
'https://gnaur.wordpress.com/2013/06/14/die-moglichkeit-nichts-zu-tun-ist-auch-eine-moglichkeit/': {
    'file': 'gnaur.wordpress.com.moglichkeit.html',
    'date': '2013-06-14',
},
'http://www.seelenradio.de/nummer-zwei-leo/': {
    'file': 'seelenradio.de.leo.html',
    'date': '2015-08-03',
},
'http://www.hertha-blog.de/der-lange-und-die-alte-dame.html': {
    'file': 'hertha-blog.de.dame.html',
    'date': '2017-07-23',
},
'http://www.echte-demokratie-jetzt.de/blog/': {
    'file': 'echte-demokratie-jetzt.de.blog.html',
    'date': '2014-01-13',
},
'https://gizmeo.eu/makrophotos-von-insekten/': {
    'file': 'gizmeo.eu.insekten.html',
    'date': '2020-01-22',
},
'https://alexanderlasch.wordpress.com/2019/11/14/was-das-christkind-und-native-americans-gemeinsam-haben-oder-warum-wir-sprachgeschichte-brauchen/': {
    'file': 'alexanderlasch.wordpress.com.sprachgeschichte.html',
    'date': '2019-11-14',
},
'https://www.alexander-klier.net/zeitenkompetenz/zeitphilosophie/': {
    'file': 'alexander-klier.net.zeitphilosophie.html',
    'date': '2012-06-08',
},
'https://2gewinnt.wordpress.com/uber-uns/': {
    'file': '2gewinnt.wordpress.com.uns.html',
    'date': '2012-06-30',
},
'http://www.buero-hoppe.de/baumgutachten.htm': {
    'file': 'buero-hoppe.de.baumgutachten.htm',
    'date': '2006-12-16',
},
}



def load_document(filename):
    '''load mock page from samples'''
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


def run_newspaper(htmlstring):
    '''try with the newspaper module'''
    ## does not work!
    myarticle = Article('https://www.example.org/test/')
    myarticle.html = htmlstring
    myarticle.download_state = ArticleDownloadState.SUCCESS
    myarticle.parse()
    if myarticle.publish_date is None:
        return None
    date = convert_date(myarticle.publish_date, '%Y-%m-%d %H:%M:%S', '%Y-%m-%d')
    return date


def run_newsplease(htmlstring):
   '''try with newsplease'''
   article = NewsPlease.from_html(htmlstring, url=None)
   if article.date_publish is None:
      return None
   date = convert_date(article.date_publish, '%Y-%m-%d %H:%M:%S', '%Y-%m-%d')
   return date


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


def calculate_scores(mydict):
    '''output weighted result score'''
    tp, fn, fp, tn = mydict['true_positives'], mydict['false_negatives'], mydict['false_positives'], mydict['true_negatives']
    precision = tp/(tp+fp)
    recall = tp/(tp+fn)
    accuracy = (tp+tn)/(tp+tn+fp+fn)
    fscore = (2*tp)/(2*tp + fp + fn)  # 2*((precision*recall)/(precision+recall))
    return precision, recall, accuracy, fscore


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


print('number of documents:', i)
print('nothing')
print(nothing)
# print(calculate_f_score(nothing))
print('htmldate extensive')
print(htmldate_extensive_result)
print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(htmldate_extensive_result)))
print('htmldate fast')
print(htmldate_fast_result)
print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(htmldate_fast_result)))
print('newspaper')
print(newspaper_result)
print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(newspaper_result)))
print('newsplease')
print(newsplease_result)
print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(newsplease_result)))
print('articledateextractor')
print(articledateextractor_result)
print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(articledateextractor_result)))
print('date_guesser')
print(dateguesser_result)
print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(dateguesser_result)))
print('goose')
print(goose_result)
print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(goose_result)))

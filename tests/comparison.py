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
'http://www.eza.gv.at/das-ministerium/presse/aussendungen/2018/07/aussenministerin-karin-kneissl-beim-treffen-der-deutschsprachigen-aussenminister-in-luxemburg/': {
    'file': 'eza.gv.at.html',
    'date': '2018-07-03',
},
'http://www.greenpeace.org/international/en/campaigns/forests/asia-pacific/': {
    'file': 'greenpeace.org.forests.html',
    'date': '2017-04-28',
},
'http://www.hobby-werkstatt-blog.de/arduino/424-eine-arduino-virtual-wall-fuer-den-irobot-roomba.php': {
    'file': 'hobby-werkstatt-blog.de.roomba.html',
    'date': '2015-12-14',
},
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
'http://www.colours-of-the-soul.alhelm.net': {
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

'https://www.pamelaandersonfoundation.org/news/2018/12/4/yellow-vests-and-i': {
    'file': 'pamelaandersonfoundation.org.yellow.html',
    'date': '2018-12-04',
},
'https://www.dbjr.de/artikel/bundespraesident-wuerdigte-das-ehrenamtliche-engagement/': {
    'file': 'dbjr.de.bundespraesident.html',
    'date': '2020-01-23',
},
'https://achtundvierzig.hypotheses.org/822': {
    'file': 'achtundvierzig.hypotheses.org.822.html',
    'date': '2015-01-28',
},
'http://bayrische-bembel.de/bbr/modules/news/article.php?storyid=504': {
    'file': 'bayrische-bembel.de.504.html',
    'date': '2015-08-25',
},
'https://ethify.org/content/vegetarier-zu-sein-bedarf-trend-oder-eigene-entscheidung': {
    'file': 'ethify.org.vegetarier.html',
    'date': '2019-07-07',
},
'https://disfunctions.de/tutorials/podcasts-in-plex-einbinden/': {
    'file': 'disfunctions.de.podcasts.html',
    'date': '2014-05-06',
},
'http://archiv.krimiblog.de/?p=2895': {
    'file': 'archiv.krimiblog.de.2895.html',
    'date': '2009-08-06',
},
'https://journal.3960.org/posts/2019-12-22-firefox-weniger-werbung-mehr-speed-unter-android/': {
    'file': 'journal.3960.org.firefox.html',
    'date': '2019-12-22',
},
'https://beyssonmanagement.com/2014/07/15/was-ist-innovation/': {
    'file': 'beyssonmanagement.com.innovation.html',
    'date': '2014-07-15',
},
'https://damianduchamps.wordpress.com/2019/08/03/office-365-hbdi-die-dritte/': {
    'file': 'damianduchamps.wordpress.com.hbdi.html',
    'date': '2019-08-03',
},
'https://sladisworld.wordpress.com/2019/12/10/was-wurde-eigentlich-aus-six-sigma/': {
    'file': 'sladisworld.wordpress.com.sigma.html',
    'date': '2019-12-10',
},
'https://www.piratenpartei-marburg.de/2019/09/21/wir-unterstuetzen-fridays-for-future/': {
    'file': 'piratenpartei-marburg.de.fridays.html',
    'date': '2019-09-21',
},
'https://www.piratenpartei.at/volksbegehren-zum-bedingungslosen-grundeinkommen-bge/': {
    'file': 'piratenpartei.at.grundeinkommen.html',
    'date': '2019-11-17',
},
'https://www.dobszay.ch/2016-04-15/was-ist-der-unterschied-zwischen-privaten-und-staatlichen-geheimdiensten/': {
    'file': 'dobszay.ch.geheimdiensten.html',
    'date': '2016-04-15',
},
'https://www.unsere-zeitung.at/2020/02/02/ist-die-inklusion-im-kapitalismus-umsetzbar/': {
    'file': 'unsere-zeitung.at.inklusion.html',
    'date': '2020-02-02',
},
'http://www.sprechwaisen.com/sw082-82-gruende-zum-weiter-hoeren/': {
    'file': 'sprechwaisen.com.sw082.html',
    'date': '2019-07-21',
},
'https://www.unterwegsinberlin.de/radtouren-berlin/radtour-durch-friedrichsfelde-karlshorst-und-schoeneweide/': {
    'file': 'unterwegsinberlin.de.friedrichsfelde.html',
    'date': '2020-02-02',
},
'https://www.strafprozess.ch/rasende-polizisten/': {
    'file': 'strafprozess.ch.polizisten.html',
    'date': '2020-02-04',
},
'https://wolfgangschmale.eu/abgebrochene-forschung-eine-neue-studie-von-heinz-duchhardt/': {
    'file': 'wolfgangschmale.eu.duchhardt.html',
    'date': '2020-02-10',
},
'https://netzfueralle.blog.rosalux.de/2019/10/30/netzpolitik-als-us-wahlkampfthema/': {
    'file': 'netzfueralle.blog.rosalux.de.netzpolitik.html',
    'date': '2019-10-30',
},
'https://www.anchor.ch/gesellschaft/ein-tag-aus-dem-leben-eines-taugenichts-oder-die-leute-von-sri-lanka/': {
    'file': 'anchor.ch.lanka.html',
    'date': '2019-12-22',
},
'https://www.ejwue.de/aktuell/news/faire-lieferketten/': {
    'file': 'ejwue.de.lieferketten.html',
    'date': '2020-02-05',
},
'https://thebigbone.wordpress.com/2017/04/13/die-ueberforderung-durch-ueberangebote/': {
    'file': 'thebigbone.wordpress.com.ueberforderung.html',
    'date': '2017-04-13',
},
'https://ritinardo.wordpress.com/2017/11/26/bundesregierung-2017-btw17-groko/': {
    'file': 'ritinardo.wordpress.com.btw17.html',
    'date': '2017-11-26',
},
'http://www.qualisys.eu/gefahrstoff-service': {
    'file': 'qualisys.eu.gefahrstoff.html',
    'date': '2019-12-19',
},
'http://www.xinhuanet.com/local/2020-02/19/c_1125597921.htm': {
    'file': 'xinhuanet.com.c_1125597921.htm',
    'date': '2020-02-19',
},
'http://www.banyuetan.org/jmcs/detail/20200102/1000200033136171577956287380194268_1.html': {
    'file': 'banyuetan.org.1000200033136171577956287380194268_1.html',
    'date': '2020-01-02',
},
'https://baike.baidu.com/item/%E8%94%A1%E5%81%A5%E9%9B%85': {
    'file': 'baike.baidu.com.tanya.html',
    'date': '2020-02-14',
},
'https://www.lastampa.it/cronaca/2020/02/19/news/temperature-in-calo-in-tutta-italia-attesa-neve-sull-appennino-1.38487954': {
    'file': 'lastampa.it.temperature.html',
    'date': '2020-02-19',
},
'https://elpais.com/elpais/2020/02/18/ciencia/1582045946_459487.html': {
    'file': 'elpais.com.ciencia.html',
    'date': '2020-02-19',
},
'https://www.latimes.com/politics/story/2020-02-19/mike-bloomberg-democratic-debate-history': {
    'file': 'latimes.com.bloomberg.html',
    'date': '2020-02-19',
},
'https://www.uusisuomi.fi/uutiset/sanna-marin-tapasi-angela-merkelin-myos-saksa-haluaa-pitaa-kiinni-maataloustuista-meidan-nakemyksiamme-suurimpana-nettomaksajana-ei-ole-otettu-riittavasti-huomioon/b29c11d3-9590-4045-8e2c-a568f9f24617': {
    'file': 'uusisuomi.fi.angela.html',
    'date': '2019-02-19',
},
'https://yle.fi/uutiset/3-11212601': {
    'file': 'yle.fi.3-11212601.html',
    'date': '2019-02-19',
},
'https://www.tofugu.com/travel/dezuka-suisan/': {
    'file': 'tofugu.com.dezuka-suisan.html',
    'date': '2020-02-04',
},
'https://blog.gaijinpot.com/tweet-of-the-week-67-dealing-with-chikan/': {
    'file': 'blog.gaijinpot.com.chikan.html',
    'date': '2020-02-08',
},
'https://madame.lefigaro.fr/bien-etre/problemes-dintestin-quoi-manger-pour-aller-bien-110417-130897': {
    'file': 'madame.lefigaro.fr.dintestin.html',
    'date': '2017-04-12',
},
'https://www.bondyblog.fr/societe/a-paris-8-un-peu-de-tension-beaucoup-d-actions/': {
    'file': 'bondyblog.fr.paris-8.html',
    'date': '2020-02-17',
},
'https://lapresse.tn/48915/parite-hommes-femmes-en-tunisie-au-dessous-de-la-moyenne-mondiale/': {
    'file': 'lapresse.tn.parite.html',
    'date': '2020-02-18',
},
'https://www.ledevoir.com/politique/montreal/573258/la-fin-des-trottinettes-en-libre-service-a-montreal': {
    'file': 'ledevoir.com.trottinettes.html',
    'date': '2020-02-19',
},

'https://wiki.piratenpartei.de/HE:Kassel/Stammtisch': {
    'file': 'wiki.piratenpartei.de.stammtisch.html',
    'date': '2020-01-29',
},
'https://aktion-hummelschutz.de/biologie/tote-hummeln-unter-linden/': {
    'file': 'aktion-hummelschutz.de.hummeln.html',
    'date': '2017-08-09',
},
'https://www.vinosytapas.de/wein/herkunft/spanien/d_o_ca_-rioja/': {
    'file': 'vinosytapas.de.rioja.html',
    'date': '2020-02-11',
},
'http://www.creativecommons.ch/wie-funktionierts/': {
    'file': 'creativecommons.ch.wie.html',
    'date': '2014-03-17',
},
'https://arsnova.thm.de/blog/frag-jetzt/': {
    'file': 'arsnova.thm.de.frag.html',
    'date': '2019-06-28',
},
'https://shabka.org/about-us/': {
    'file': 'shabka.org.about.html',
    'date': '2018-06-07',
},
'https://www.parallels.com/products/desktop/': {
    'file': 'parallels.com.desktop.html',
    'date': '2020-02-03',
},
'https://taz.de/Siemens-und-die-Kohlemine-Adani/!5655255/': {
    'file': 'taz.de.siemens.html',
    'date': '2020-01-13',
},
'https://fivethirtyeight.com/features/the-2020-endorsement-race-is-getting-interesting/': {
    'file': 'fivethirtyeight.com.endorsement.html',
    'date': '2020-01-28',
},
'https://www.wired.com/story/ai-great-things-burn-planet/': {
    'file': 'wired.com.burn.html',
    'date': '2020-01-21',
},
'http://www.parcoabruzzo.it/dettaglio.php?id=58354': {
    'file': 'parcoabruzzo.it.58354.html',
    'date': '2020-01-14',
},
'https://www.timesofisrael.com/state-of-washington-swears-in-first-native-american-jewish-supreme-court-justice/': {
    'file': 'timesofisrael.com.washington.html',
    'date': '2020-01-08',
},
'https://www.scmp.com/comment/opinion/article/3046526/taiwanese-president-tsai-ing-wens-political-playbook-should-be': {
    'file': 'scmp.com.playbook.html',
    'date': '2020-01-20',
},
'https://medium.com/@ransu.massol/recherche-non-%C3%A0-une-loi-in%C3%A9galitaire-be507f7cf761': {
    'file': 'medium.com.recherche.html',
    'date': '2019-12-09',
},
'https://juliasleseblog.blogspot.com/2018/08/irland-roadtrip.html': {
    'file': 'juliasleseblog.blogspot.com.irland.html',
    'date': '2018-08-02',
},
'https://literaturgefluester.wordpress.com/2019/01/01/ins-neue-jahr-4/': {
    'file': 'literaturgefluester.wordpress.com.jahr.html',
    'date': '2019-01-01',
},
'https://abookshelffullofsunshine.blogspot.com/2013/10/news-viertes-eigenes-blog-interview.html': {
    'file': 'abookshelffullofsunshine.blogspot.com.interview.html',
    'date': '2013-10-05',
},
'https://www.derpapierplanet.de/2015/06/through-booking-glass-juni-genre.html': {
    'file': 'derpapierplanet.de.juni.html',
    'date': '2015-06-05',
},
'https://weinlachgummis.blogspot.com/2017/09/rezi-love-is-war-sehnsucht-von-r-k.html': {
    'file': 'weinlachgummis.blogspot.com.rezi.html',
    'date': '2017-09-09',
},
'https://happyface313.com/2018/03/07/im-test-plantur-39-color-braun-phyto-coffein-shampoo-und-pflege-spulung/': {
    'file': 'happyface313.com.plantur.html',
    'date': '2018-03-07',
},
'https://www.limespace.de/2019/10/22/professionell-entloeten-so-machen-sie-alte-elektrogeraete-wieder-einsatzbereit/': {
    'file': 'limespace.de.entloeten.html',
    'date': '2019-10-22',
},
'https://frau-sabienes.de/konsumsparen-fazit/': {
    'file': 'frau-sabienes.de.konsumsparen.html',
    'date': '2020-02-17',
},
'http://lexikon.huettenhilfe.de/obst/banane.html': {
    'file': 'lexikon.huettenhilfe.de.banane.html',
    'date': '2011-07-25',
},
'https://de.happycoffee.org/collections/shop/products/happy-coffee-sidamo-bio-kaffeebohnen': {
    'file': 'de.happycoffee.org.sidamo.html',
    'date': '2019-03-02',
},
'https://www.spektrum.de/wissen/laesst-sich-die-coronavirus-ausbreitung-in-deutschland-kontrollieren/1700384': {
    'file': 'spektrum.de.coronavirus.html',
    'date': '2020-02-26',
},
'https://www.talent.ch/?p=5031': {
    'file': 'talent.ch.5031.html',
    'date': '2019-12-26',
},
'https://www.pronats.de/informationen/kindheit-und-arbeit/kinder-und-arbeit/': {
    'file': 'pronats.de.arbeit.html',
    'date': '2016-12-30',
},
'https://www.tafelblog.de/welches-europa-wir-wollen/': {
    'file': 'tafelblog.de.europa.html',
    'date': '2019-06-11',
},
'http://columbus-entdeckt.de/ski-fahren-auf-den-spuren-des-trolls/': {
    'file': 'columbus-entdeckt.de.trolls.html',
    'date': '2020-01-05',
},
'https://www.advents-shopping.de/die-weihnachtsmarkt-saison-beginnt-so-finden-sie-die-besten-weihnachtsmaerkte-in-ihrer-naehe.html': {
    'file': 'advents-shopping.de.weihnachtsmaerkte.html',
    'date': '2014-11-02',
},
'https://bloghaus.hypotheses.org/2320': {
    'file': 'bloghaus.hypotheses.org.2320.html',
    'date': '2019-09-26',
},
'http://www.der-erfolg-gibt-recht.de/rezepte/rinderleber-geschnetzeltes-mit-apfel-und-zwiebel.htm': {
    'file': 'der-erfolg-gibt-recht.de.rinderleber.html',
    'date': '2010-12-08',
},
'https://tell-review.de/unstillbares-heimweh/': {
    'file': 'tell-review.de.heimweh.html',
    'date': '2019-09-18',
},
'https://it-for-kids.org/blog/191211_variables/': {
    'file': 'it-for-kids.org.variables.html',
    'date': '2019-12-11',
},
'http://papaganda.org/2016/04/02/minions-mit-schablonen-malen-mit-malerrolle-und-bunten-farben/': {
    'file': 'papaganda.org.minions.html',
    'date': '2016-04-02',
},
'http://marktplatz.die-besserwisser.org/alles-hat-seine-zeit/': {
    'file': 'marktplatz.die-besserwisser.org.zeit.html',
    'date': '2017-04-05',
},
'https://www.doschu.com/2020/02/solopreneur-social-media-linkedin/': {
    'file': 'doschu.com.solopreneur.html',
    'date': '2020-02-14',
},
'https://blog.teufel.de/musik-und-sport-so-steigern-songs-deine-leistung/': {
    'file': 'blog.teufel.de.leistung.html',
    'date': '2020-02-13',
},
'https://www.whiskyverkostung.com/termine-whisky-tastings-januar-mai-2020-halle-saale/5805': {
    'file': 'whiskyverkostung.com.halle.html',
    'date': '2019-11-27',
},
'https://zahlenzauberin.wordpress.com/2012/08/22/was-zum-horen-in-den-ferien/': {
    'file': 'zahlenzauberin.wordpress.com.ferien.html',
    'date': '2010-08-22',
},
'https://www.deutschlandfunk.de/die-zukunft-der-arbeit-wir-dekorieren-auf-der-titanic-die.911.de.html?dram:article_id=385022': {
    'file': 'deutschlandfunk.de.titanic.html',
    'date': '2017-05-01',
},
'https://1hundetagebuch.wordpress.com/2019/10/31/nach-viel-zu-langer-zeit-mal-wieder/': {
    'file': '1hundetagebuch.wordpress.com.langer.html',
    'date': '2019-10-31',
},
'http://www.steinhau.com/steinhau/wordpress/einmal-zahlen-alles-lesen/': {
    'file': 'steinhau.com.zahlen.html',
    'date': '2019-11-13',
},
'http://www.pointofsail-kiel.de/artikel/ben-wilson-surf.html': {
    'file': 'pointofsail-kiel.de.wilson.html',
    'date': '2019-06-20',
},
'http://www.interscenar.io/politik/eindruecke/was-wir-ueber-uns-nicht-hoeren-wollen': {
    'file': 'interscenar.io.hoeren.html',
    'date': '2019-03-03',
},
'https://www.deviante-pfade.de/unbefriedigt/': {
    'file': 'deviante-pfade.de.unbefriedigt.html',
    'date': '2020-01-08',
},
'https://seglerblog.stössenseer.de/haltet-unsere-gewaesser-sauber/': {
    'file': 'seglerblog.stössenseer.de.sauber.html',
    'date': '2020-02-23',
},
'https://www.ihrwebprofi.at/2011/09/17/publikumsvoting-beim-wiener-content-award-gestartet/': {
    'file': 'ihrwebprofi.at.publikumsvoting.html',
    'date': '2011-09-17',
},
'https://mitternachtskabinett.wordpress.com/2016/06/19/geister-spuk-gentrifizierung/': {
    'file': 'mitternachtskabinett.wordpress.com.gentrifizierung.html',
    'date': '2016-06-19',
},
'http://www.aussengedanken.de/streit-ums-feuerholz/': {
    'file': 'aussengedanken.de.feuerholz.html',
    'date': '2017-02-13',
},
'https://insubordinant.wordpress.com/2015/08/11/need-for-speed/': {
    'file': 'insubordinant.wordpress.com.speed.html',
    'date': '2015-08-11',
},
'http://rueda.wikidot.com/enchufla': {
    'file': 'rueda.wikidot.com.enchufla.html',
    'date': '2008-03-23',
},
'https://zulang.wordpress.com/2015/12/12/3-jahre-legalisierte-genitalverstuemmelung/': {
    'file': 'zulang.wordpress.com.genitalverstuemmelung.html',
    'date': '2015-12-12',
},
'https://surfguard.wordpress.com/2016/11/01/ich-las-sah-hoerte-medien-im-oktober-2016/': {
    'file': 'surfguard.wordpress.com.medien.html',
    'date': '2016-11-01',
},
'https://litradio.net/die-autorin-nora-bossong-im-gespraech-ueber-ihren-roman-schutzzone/': {
    'file': 'litradio.net.bossong.html',
    'date': '2020-02-22',
},
'https://www.japantimes.co.jp/news/2020/02/18/national/crime-legal/6000-surgical-masks-stolen/': {
    'file': 'japantimes.co.jp.surgical.html',
    'date': '2020-02-18',
},
'http://www.hearya.com/2006/12/04/hit-paraders-top-100-metal-vocalists-of-all-time/': {
    'file': 'hearya.com.metal.html',
    'date': '2006-12-04',
},
'http://thenervousbreakdown.com/tanderson/2011/07/the-loneliest-woman-in-the-world-an-appreciation-of-hearts-alone/': {
    'file': 'thenervousbreakdown.com.loneliest.html',
    'date': '2011-07-11',
},
'https://www.cbsnews.com/news/2020-presidential-election-south-carolina-black-voters-democrats-joe-biden/': {
    'file': 'cbsnews.com.carolina.html',
    'date': '2020-02-24',
},
'https://pagesix.com/2020/02/24/former-wh-press-secretary-dee-dee-myers-exits-warner-bros-role/': {
    'file': 'pagesix.com.myers.html',
    'date': '2020-02-24',
},
'https://tonedeaf.thebrag.com/record-of-the-week-luboku-pale-blue-dot-lift-off/': {
    'file': 'tonedeaf.thebrag.com.luboku.html',
    'date': '2020-02-21',
},
'https://it-learner.de/wenn-das-netzwerk-unter-windows-10-sehr-langsam-ist-koennte-das-abschalten-der-autotuning-funktion-abhilfe-schaffen/': {
    'file': 'it-learner.de.autotuning.html',
    'date': '2019-05-16',
},
'https://de.induux.com/4press/energiezaehler-m-bus-mod-bus-ethernet-mid-3999/': {
    'file': 'de.induux.com.energiezaehler.html',
    'date': '2018-04-20',
},
'https://aoc.media/opinion/2019/12/09/pour-le-neoliberalisme-la-retraite-est-un-archaisme/': {
    'file': 'aoc.media.archaisme.html',
    'date': '2019-12-10',
},
'http://www.regards.fr/politique/article/deux-ans-et-demi-en-macronie-9-mises-en-examen-10-enquetes-en-cours-et-2': {
    'file': 'regards.fr.enquetes.html',
    'date': '2018-09-30',
},
'https://newrepublic.com/article/155970/collapse-neoliberalism': {
    'file': 'newrepublic.com.neoliberalism.html',
    'date': '2019-12-23',
},
'https://www.tdg.ch/suisse/berne-interdit-chlorothalonil/story/18348200': {
    'file': 'tdg.ch.chlorothalonil.html',
    'date': '2019-12-12',
},
'https://www.gala.fr/l_actu/news_de_stars/jean-paul-delevoye-monsieur-retraites-du-gouvernement-jacques-chirac-lui-donnait-un-surnom-peu-flatteur_439447': {
    'file': 'gala.fr.surnom.html',
    'date': '2019-12-09',
},
'https://www.elle.de/plateau-sneaker-trend': {
    'file': 'elle.de.sneaker.html',
    'date': '2019-06-19',
},
'https://www.faz.net/aktuell/reise/reise-durch-sierra-leone-es-ist-zeit-fuer-den-tourismus-16306548.html': {
    'file': 'faz.net.leone.html',
    'date': '2019-07-30',
},
'https://www.management-circle.de/blog/remote-support-mit-smart-glasses/': {
    'file': 'management-circle.de.glasses.html',
    'date': '2019-07-25',
},
'https://www.it-finanzmagazin.de/creditshelf-kooperiert-mit-finleap-und-plant-akquisition-der-valendo-gmbh-90871/': {
    'file': 'it-finanzmagazin.de.creditshelf.html',
    'date': '2019-06-20',
},
'https://abenteuer-astronomie.de/astrofoto-community/plejaden-m45-2/': {
    'file': 'abenteuer-astronomie.de.plejaden.html',
    'date': '2019-09-17',
},
'https://www.soundofscience.fr/1927': {
    'file': 'soundofscience.fr.1927.html',
    'date': '2020-01-20',
},
'https://www.theguardian.com/education/2020/jan/20/thousands-of-uk-academics-treated-as-second-class-citizens': {
    'file': 'theguardian.com.academics.html',
    'date': '2020-01-20',
},
'https://phys.org/news/2019-10-flint-flake-tool-partially-birch.html': {
    'file': 'phys.org.tool.html',
    'date': '2019-10-22',
},
'https://laviedesidees.fr/L-evaluation-et-les-listes-de.html': {
    'file': 'laviedesidees.fr.evaluation.html',
    'date': '2009-09-15',
},
'https://gregoryszorc.com/blog/2020/01/13/mercurial%27s-journey-to-and-reflections-on-python-3/': {
    'file': 'gregoryszorc.com.python3.html',
    'date': '2020-01-13',
},
'https://www.pluralsight.com/tech-blog/managing-python-environments/': {
    'file': 'pluralsight.com.python.html',
    'date': '2020-01-10',
},
'https://stackoverflow.blog/2020/01/20/what-is-rust-and-why-is-it-so-popular/': {
    'file': 'stackoverflow.com.rust.html',
    'date': '2020-01-20',
},
'https://www.theplanetarypress.com/2020/01/management-of-intact-forestlands-by-indigenous-peoples-key-to-protecting-climate/': {
    'file': 'theplanetarypress.com.forestlands.html',
    'date': '2020-01-19',
},
'https://wikimediafoundation.org/news/2020/01/15/access-to-wikipedia-restored-in-turkey-after-more-than-two-and-a-half-years/': {
    'file': 'wikimediafoundation.org.turkey.html',
    'date': '2020-01-15',
},
'https://www.reuters.com/article/us-awards-sag/parasite-scores-upset-at-sag-awards-boosting-oscar-chances-idUSKBN1ZI0EH': {
    'file': 'reuters.com.parasite.html',
    'date': '2020-01-19',
},
'https://www.nationalgeographic.co.uk/environment-and-conservation/2020/01/ravenous-wild-goats-ruled-island-over-century-now-its-being': {
    'file': 'nationalgeographic.co.uk.goats.html',
    'date': '2020-01-06',
},
'https://www.nature.com/articles/d41586-019-02790-3': {
    'file': 'nature.com.telescope.html',
    'date': '2019-09-24',
},
'https://www.salon.com/2020/01/10/despite-everything-u-s-emissions-dipped-in-2019_partner/': {
    'file': 'salon.com.emissions.html',
    'date': '2020-01-10',
},
}
#'https://en.support.wordpress.com/': {
#    'file': 'support.wordpress.com.html',
#    'date': None,
#},
#'https://exporo.de/wiki/europaeische-zentralbank-ezb/': {
#    'file': 'exporo.de.ezb.html',
#    'date': '',
#},
#'https://www.beltz.de/sachbuch_ratgeber/buecher/produkt_produktdetails/37219-12_wege_zu_guter_pflege.html': {
#    'file': 'beltz.de.12wege.html',
#    'date': '',
#},
#'http://www.hundeverein-kreisunna.de/termine.html': {
#    'file': 'hundeverein-kreisunna.de.html',
#    'date': '',
#},
#'http://www.hundeverein-querfurt.de/index.php?option=com_content&view=article&id=54&Itemid=50': {
#    'file': 'hundeverein-querfurt.de.html',
#    'date': '',
#},
#'https://www.intel.com/content/www/us/en/legal/terms-of-use.html': {
#    'file': 'intel.com.tos.html',
#    'date': None,
#},
#'http://www.heimicke.de/chronik/zahlen-und-daten/': {
#    'file': 'heimicke.de.zahlen.html',
#    'date': '',
#},
#'http://viehbacher.com/de/spezialisierung/internationale-forderungsbeitreibung': {
#    'file': 'viehbacher.com.forderungsbetreibung.html',
#    'date': '',
#},


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
print("time diff.: %.2f" % (htmldate_extensive_result['time'] / htmldate_fast_result['time']))
print('htmldate fast')
print(htmldate_fast_result)
print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(htmldate_fast_result)))
print("time diff.: %.2f" % (htmldate_fast_result['time'] / htmldate_fast_result['time']))
print('newspaper')
print(newspaper_result)
print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(newspaper_result)))
print("time diff.: %.2f" % (newspaper_result['time'] / htmldate_fast_result['time']))
print('newsplease')
print(newsplease_result)
print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(newsplease_result)))
print("time diff.: %.2f" % (newsplease_result['time'] / htmldate_fast_result['time']))
print('articledateextractor')
print(articledateextractor_result)
print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(articledateextractor_result)))
print("time diff.: %.2f" % (articledateextractor_result['time'] / htmldate_fast_result['time']))
print('date_guesser')
print(dateguesser_result)
print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(dateguesser_result)))
print("time diff.: %.2f" % (dateguesser_result['time'] / htmldate_fast_result['time']))
print('goose')
print(goose_result)
print('precision: %.3f recall: %.3f accuracy: %.3f f-score: %.3f' % (calculate_scores(goose_result)))
print("time diff.: %.2f" % (goose_result['time'] / htmldate_fast_result['time']))

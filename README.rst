htmldate: find the creation date of HTML pages
==============================================

.. image:: https://img.shields.io/pypi/v/htmldate.svg
    :target: https://pypi.python.org/pypi/htmldate

.. image:: https://img.shields.io/pypi/l/htmldate.svg
    :target: https://pypi.python.org/pypi/htmldate

.. image:: https://img.shields.io/pypi/pyversions/htmldate.svg
    :target: https://pypi.python.org/pypi/htmldate

.. image:: https://img.shields.io/travis/adbar/htmldate.svg
    :target: https://travis-ci.org/adbar/htmldate

.. image:: https://img.shields.io/codecov/c/github/adbar/htmldate.svg
    :target: https://codecov.io/gh/adbar/htmldate


This library finds the creation date of web pages using a combination of tree traversal, common structural patterns, text-based heuristics and robust date extraction. It can handle all the steps needed from web page download to HTML parsing, including scraping and textual analysis. It takes URLs, HTML files or HTML trees as input and outputs a date.


.. contents:: **Contents**
    :backlinks: none


Features
--------

Seamless extraction of the creation or modification date of web pages: given a HTML document, *htmldate* provides following ways to date it, based on HTML parsing, scraping functions, and robust date parsing:

1. Starting from the header of the page, it uses common patterns to identify date fields (e.g. ``link`` and ``meta`` elements) including `Open Graph protocol <http://ogp.me/>`_ attributes and a large number of CMS idiosyncracies
2. If this is not successful, it scans the whole document looking for structural markers: ``abbr``/``time`` elements and a series of attributes (e.g. ``postmetadata``)
3. If no date cue could be found, it finally runs a series of heuristics on the content (text and markup):

  1. in ``fast`` mode, the HTML page is cleaned and precise expressions are searched for
  2. in the more opportunistic default setting, date expressions are collected and the best one is chosen based on a disambiguation algorithm

The module then returns a date if a valid cue could be found in the document, per default the updated date w.r.t. the original publishing statement.  The output string defaults to `ISO 8601 YMD format <https://en.wikipedia.org/wiki/ISO_8601>`_.

-  Should be compatible with all common versions of Python 3 (see tests and coverage)
-  Safety belt included, the output is thouroughly verified with respect to its plausibility and adequateness
-  Designed to be computationally efficient and is used in production on millions of documents
-  Handles batch processing of a list of URLs

The library currently focuses on texts in written English or German.


Installation
------------

Install from package repository: ``pip install htmldate``

Direct installation of the latest version over pip is possible (see `build status <https://travis-ci.org/adbar/htmldate>`_):

``pip install git+https://github.com/adbar/htmldate.git``


On the command-line
-------------------

A basic command-line interface is included:

.. code-block:: bash

    $ htmldate -u http://blog.python.org/2016/12/python-360-is-now-available.html
    '2016-12-23'
    $ wget -qO- "http://blog.python.org/2016/12/python-360-is-now-available.html" | htmldate
    '2016-12-23'

For usage instructions see ``htmldate -h``:

.. code-block:: bash

    $ htmldate --help
    htmldate [-h] [-v] [-f] [-i INPUTFILE] [-u URL]
    optional arguments:
        -h, --help     show this help message and exit
        -v, --verbose  increase output verbosity
        -f, --fast     fast mode: disable extensive search
        --original     original date prioritized
        -i INPUTFILE, --inputfile INPUTFILE
                             name of input file for batch processing (similar to
                             wget -i)
        -u URL, --URL URL     custom URL download

The batch mode ``-i`` takes one URL per line as input and returns one result per line in tab-separated format:

.. code-block:: bash

    $ htmldate -fv -i list-of-urls.txt


With Python
-----------

All the functions of the module are currently bundled in *htmldate*.

In case the web page features easily readable metadata in the header, the extraction is straightforward. A more advanced analysis of the document structure is sometimes needed:

.. code-block:: python

    >>> htmldate.find_date('http://blog.python.org/2016/12/python-360-is-now-available.html')
    '# DEBUG analyzing: <h2 class="date-header"><span>Friday, December 23, 2016</span></h2>'
    '# DEBUG result: 2016-12-23'
    '2016-12-23'

In the worst case, the module resorts to a guess based on a complete screning of the document (``extensive_search`` parameter) which can be deactivated:

.. code-block:: python

    >>> htmldate.find_date('https://creativecommons.org/about/')
    '2017-08-11' # has been updated since
    >>> htmldate.find_date('https://creativecommons.org/about/', extensive_search=False)
    >>>


Input format
~~~~~~~~~~~~

The module expects strings as shown above, it is also possible to use already parsed HTML (i.e. a LXML tree object):

.. code-block:: python

    >>> from lxml import html
    >>> mytree = html.fromstring('<html><body><span class="entry-date">July 12th, 2016</span></body></html>')
    >>> htmldate.find_date(mytree)
    '2016-07-12'

An external module can be used for download, as described in versions anterior to 0.3. This example uses the legacy mode with `requests <http://docs.python-requests.org/>`_ as external module.

.. code-block:: python

    >>> import htmldate, requests
    >>> r = requests.get('https://creativecommons.org/about/')
    >>> htmldate.find_date(r.text)
    '2017-11-28' # may have changed since


Date format
~~~~~~~~~~~

The output format of the dates found can be set in a format known to Python's ``datetime`` module, the default being ``%Y-%m-%d``:

.. code-block:: python

    >>> htmldate.find_date('https://www.gnu.org/licenses/gpl-3.0.en.html', outputformat='%d %B %Y')
    '18 November 2016' # may have changed since


Original date
~~~~~~~~~~~~~

Although the time delta between the original publication and the "last modified" statement is usually a matter of hours or days at most, it can be useful in some contexts to prioritize the original publication date during extraction:

.. code-block:: python

    >>> htmldate.find_date('https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/') # default setting
    '2019-06-24'
    >>> htmldate.find_date('https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/', original_bool=True) # modified behavior
    '2016-06-23'


Language-specific analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~

The expected date format can be tweaked to suit particular needs, especially language-specific date expressions, beyond the current scope (English and German): see the init part of ``core.py`` as well as `the dateparser docs <https://dateparser.readthedocs.io/en/latest/>`_ for more information (example setting: ``dateparser.DateDataParser(settings={'PREFER_DAY_OF_MONTH': 'first', 'PREFER_DATES_FROM': 'past', 'DATE_ORDER': 'DMY'}``).


Known caveats
~~~~~~~~~~~~~

The granularity may not always match the desired output format. If only information about the year could be found and the chosen date format requires to output a month and a day, the result is 'padded' to be located at the middle of the year, in that case the 1st of January.

Besides, there are pages for which no date can be found, ever:

.. code-block:: python

    >>> r = requests.get('https://example.com')
    >>> htmldate.find_date(r.text)
    >>>


Tests
~~~~~

A series of webpages triggering different structural and content patterns is included for testing purposes:

.. code-block:: bash

    $ python tests/unit_tests.py

For more comprehensive tests ``tox`` is also an option (see ``tox.ini``).


Additional information
----------------------

Context
~~~~~~~

This module is part of methods to derive metadata from web documents in order to build text corpora for computational linguistic and NLP analysis, the original problem being that there are web pages for which neither the URL nor the server response provide a reliable way to date the document, i.e. find when it was first published and/or last modified. For more information:

-  Barbaresi, Adrien. "`Efficient construction of metadata-enhanced web corpora <https://hal.archives-ouvertes.fr/hal-01371704v2/document>`_", Proceedings of the `10th Web as Corpus Workshop (WAC-X) <https://www.sigwac.org.uk/wiki/WAC-X>`_, 2016.


Kudos to...
~~~~~~~~~~~

-  `cchardet <https://github.com/PyYoshi/cChardet>`_
-  `ciso8601 <https://github.com/closeio/ciso8601>`_
-  `lxml <http://lxml.de/>`_
-  `dateparser <https://github.com/scrapinghub/dateparser>`_ (although it is a bit slow)
-  A few patterns are derived from `python-goose <https://github.com/grangier/python-goose>`_, `metascraper <https://github.com/ianstormtaylor/metascraper>`_, `newspaper <https://github.com/codelucas/newspaper>`_ and `articleDateExtractor <https://github.com/Webhose/article-date-extractor>`_. This module extends their coverage and robustness significantly.


Going further
~~~~~~~~~~~~~

If the date is nowhere to be found, it might be worth considering `carbon dating <https://github.com/oduwsdl/CarbonDate>`_ the web page, however this is computationally expensive.

Pull requests are welcome.


Contact
~~~~~~~

See my `contact page <http://adrien.barbaresi.eu/contact.html>`_ for details.

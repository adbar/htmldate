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


This module can handle all the steps needed from web page download to HTML parsing, including scraping and textual analysis. Its goal is to find the creation date of a page all common structural patterns, text-based heuristics and robust date extraction. It takes URLs, HTML files or trees as input and outputs a date.


.. contents:: **Contents**
    :backlinks: none


Features
--------

Seamless extraction of the creation or modification date of web pages. *htmldate* provides following ways to date documents, based on HTML parsing and scraping functions and on robust date parsing:

1. Starting from the header of the page, it uses common patterns to identify date fields: ``link`` and ``meta`` elements, including `Open Graph protocol <http://ogp.me/>`_ attributes and a large number of CMS idiosyncracies
2. If this is not successful, it scans the whole document looking for structural markers: ``abbr``/``time`` elements and a series of attributes (e.g. ``postmetadata``)
3. If no date cue could be found, it finally runs a series of heuristics on the content (text and markup).

The module takes the HTML document as input (string format) and returns a date if a valid cue could be found in the document. The output string defaults to `ISO 8601 YMD format <https://en.wikipedia.org/wiki/ISO_8601>`_.

-  Should be compatible with all common versions of Python (see tests and coverage)
-  Safety belt included, the output is thouroughly verified with respect to its plausibility and adequateness
-  Designed to be computationally efficient and is used in production on millions of documents


Installation
------------

Install from package repository: ``pip install htmldate``

Direct installation of the latest version over pip is possible (see `build status <https://travis-ci.org/adbar/htmldate>`_):

``pip install git+https://github.com/adbar/htmldate.git``


On the command-line
-------------------

A basic command-line interface is included:

.. code-block:: bash

    $ wget -qO- "http://blog.python.org/2016/12/python-360-is-now-available.html" | htmldate
    '2016-12-23'

For usage instructions see ``htmldate -h``:

.. code-block:: bash

    $ htmldate --help
    htmldate [-h] [-v] [-s]
    optional arguments:
        -h, --help     show this help message and exit
        -v, --verbose  increase output verbosity
        -s, --safe     safe mode: markup search only
        -i INPUTFILE, --inputfile INPUTFILE
                       name of input file for batch processing

The batch mode ``-i`` is similar to ``wget -i``, it takes one URL per line as input and returns one result per line in tab-separated format:

.. code-block:: bash

    $ htmldate -sv -i list-of-urls.txt


With Python
-----------

All the functions of the module are currently bundled in *htmldate*.

In case the web page features easily readable metadata in the header, the extraction is straightforward. A more advanced analysis of the document structure is sometimes needed:

.. code-block:: python

    >>> htmldate.find_date('http://blog.python.org/2016/12/python-360-is-now-available.html')
    '# DEBUG analyzing: <h2 class="date-header"><span>Friday, December 23, 2016</span></h2>'
    '# DEBUG result: 2016-12-23'
    '2016-12-23'

In the worst case, the module resorts to a guess based on an extensive search, which can be deactivated:

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


Language-specific analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~

The expected date format can be tweaked to suit particular needs, especially language-specific date expressions:

.. code-block:: python

    >>> htmldate.find_date(r.text, dparser=dateparser_object) # like dateparser.DateDataParser(settings={'PREFER_DAY_OF_MONTH': 'first', 'PREFER_DATES_FROM': 'past', 'DATE_ORDER': 'DMY'}

See the init part of ``core.py`` as well as `the dateparser docs <https://dateparser.readthedocs.io/en/latest/>`_ for more information.


Known caveats
~~~~~~~~~~~~~

The granularity may not always match the desired output format. If only information about the year could be found and the chosen date format requires to output a month and a day, the result is 'padded' to be located at the middle of the year, in that case the 1st of July.

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

-  Barbaresi, Adrien. "`Efficient construction of metadata-enhanced web corpora <https://hal.archives-ouvertes.fr/hal-01348706/document>`_", Proceedings of the `10th Web as Corpus Workshop (WAC-X) <https://www.sigwac.org.uk/wiki/WAC-X>`_, 2016.


Kudos to...
~~~~~~~~~~~

-  `lxml <http://lxml.de/>`_
-  `dateparser <https://github.com/scrapinghub/dateparser>`_ (although it's is still a bit slow)
-  A few patterns are derived from `python-goose <https://github.com/grangier/python-goose>`_, `metascraper <https://github.com/ianstormtaylor/metascraper>`_, `newspaper <https://github.com/codelucas/newspaper>`_ and `articleDateExtractor <https://github.com/Webhose/article-date-extractor>`_. This module extends their coverage and robustness significantly.


Going further
~~~~~~~~~~~~~

If the date is nowhere to be found, it might be worth considering `carbon dating <https://github.com/oduwsdl/CarbonDate>`_ the web page, however this is computationally expensive.

Pull requests are welcome.


Contact
~~~~~~~

See my `contact page <http://adrien.barbaresi.eu/contact.html>`_ for details.

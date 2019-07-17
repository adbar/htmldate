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


:Code:           https://github.com/adbar/htmldate
:Documentation:  https://htmldate.readthedocs.io
:Issue tracker:  https://github.com/adbar/htmldate/issues


In a nutshell:

.. code-block:: python

    >>> from htmldate import find_date
    >>> find_date('http://blog.python.org/2016/12/python-360-is-now-available.html')
    '2016-12-23'
    >>> find_date('https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/', original_date=True)
    '2016-06-23'

.. code-block:: bash

    $ htmldate -u http://blog.python.org/2016/12/python-360-is-now-available.html
    '2016-12-23'


.. contents:: **Contents**
    :backlinks: none


Features
--------

*htmldate* finds the creation date of web pages using a combination of tree traversal, common structural patterns, text-based heuristics and robust date extraction. All the steps needed from web page download to HTML parsing, including scraping and textual analysis are handled. URLs, HTML files or HTML trees are given as input, the library outputs a date string in the desired format.

*htmldate* provides following ways to date a HTML document:

1. **Markup in header**: common patterns are used to identify relevant elements (e.g. ``link`` and ``meta`` elements) including `Open Graph protocol <http://ogp.me/>`_ attributes and a large number of CMS idiosyncracies
2. **HTML code**: The whole document is then searched for structural markers: ``abbr``/``time`` elements and a series of attributes (e.g. ``postmetadata``)
3. **Bare HTML content**: A series of heuristics is run on text and markup:

  1. in ``fast`` mode the HTML page is cleaned and precise patterns are targeted
  2. in ``extensive`` mode date expressions are collected and the best one is chosen based on a disambiguation algorithm

The module then returns a date if a valid cue could be found in the document, per default the updated date w.r.t. the original publishing statement. The output string defaults to `ISO 8601 YMD format <https://en.wikipedia.org/wiki/ISO_8601>`_.

-  Should be compatible with all common versions of Python 3 (see tests and coverage)
-  Safety belt included, the output is thouroughly verified with respect to its plausibility and adequateness
-  Designed to be computationally efficient and used in production on millions of documents
-  Handles batch processing of a list of URLs

The library currently focuses on texts written in English or German.


Installation
------------

Install from package repository: ``pip install htmldate``

For the latest version (check `build status <https://travis-ci.org/adbar/htmldate>`_): ``pip install git+https://github.com/adbar/htmldate.git``


With Python
-----------

.. code-block:: python

    >>> from htmldate import find_date
    >>> find_date('http://blog.python.org/2016/12/python-360-is-now-available.html')
    '2016-12-23'

The module can resort to a guess based on a complete screning of the document (``extensive_search`` parameter) which can be deactivated:

.. code-block:: python

    >>> find_date('https://creativecommons.org/about/')
    '2017-08-11' # has been updated since
    >>> find_date('https://creativecommons.org/about/', extensive_search=False)
    >>>


Input format
~~~~~~~~~~~~

The module expects strings as shown above, it is also possible to use already parsed HTML (i.e. a LXML tree object):

.. code-block:: python

    # simple HTML document as string
    >>> htmldoc = '<html><body><span class="entry-date">July 12th, 2016</span></body></html>'
    >>> find_date(mytree)
    '2016-07-12'
    # parsed LXML tree
    >>> from lxml import html
    >>> mytree = html.fromstring('<html><body><span class="entry-date">July 12th, 2016</span></body></html>')
    >>> find_date(mytree)
    '2016-07-12'


Date format
~~~~~~~~~~~

The output format of the dates found can be set in a format known to Python's ``datetime`` module, the default being ``%Y-%m-%d``:

.. code-block:: python

    >>> find_date('https://www.gnu.org/licenses/gpl-3.0.en.html', outputformat='%d %B %Y')
    '18 November 2016' # may have changed since


Original date
~~~~~~~~~~~~~

Although the time delta between the original publication and the *last modified* statement is usually a matter of hours or days at most, it can be useful in some contexts to prioritize the original publication date during extraction:

.. code-block:: python

    >>> find_date('https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/') # default setting
    '2019-06-24'
    >>> find_date('https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/', original_date=True) # modified behavior
    '2016-06-23'


On the command-line
-------------------

A basic command-line interface is included:

.. code-block:: bash

    $ htmldate -u http://blog.python.org/2016/12/python-360-is-now-available.html
    '2016-12-23'

For usage instructions see ``htmldate -h``:

The batch mode ``-i`` takes one URL per line as input and returns one result per line in tab-separated format:

.. code-block:: bash

    $ htmldate -i list-of-urls.txt


Additional information
----------------------

Going further
~~~~~~~~~~~~~

For more details check the online documentation: `htmldate.readthedocs.io <https://htmldate.readthedocs.io/>`_

If the date is nowhere to be found, it might be worth considering `carbon dating <https://github.com/oduwsdl/CarbonDate>`_ the web page, however this is computationally expensive. In addition, `datefinder <https://github.com/akoumjian/datefinder>`_ features pattern-based date extraction for texts written in English.

`Pull requests <https://help.github.com/en/articles/about-pull-requests>`_ are welcome.

Context
~~~~~~~

This module is part of methods to derive metadata from web documents in order to build text corpora for computational linguistic and NLP analysis, the original problem being that there are web pages for which neither the URL nor the server response provide a reliable way to date the document, i.e. find when it was first published and/or last modified. For more information:

-  Barbaresi, Adrien. "`Efficient construction of metadata-enhanced web corpora <https://hal.archives-ouvertes.fr/hal-01371704v2/document>`_", Proceedings of the `10th Web as Corpus Workshop (WAC-X) <https://www.sigwac.org.uk/wiki/WAC-X>`_, 2016.

Kudos to...
~~~~~~~~~~~

-  `cchardet <https://github.com/PyYoshi/cChardet>`_, `ciso8601 <https://github.com/closeio/ciso8601>`_, `lxml <http://lxml.de/>`_, `dateparser <https://github.com/scrapinghub/dateparser>`_ (although it is a bit slow)
-  A few patterns are derived from `python-goose <https://github.com/grangier/python-goose>`_, `metascraper <https://github.com/ianstormtaylor/metascraper>`_, `newspaper <https://github.com/codelucas/newspaper>`_ and `articleDateExtractor <https://github.com/Webhose/article-date-extractor>`_. This module extends their coverage and robustness significantly.

Contact
~~~~~~~

See my `contact page <http://adrien.barbaresi.eu/contact.html>`_ for details.

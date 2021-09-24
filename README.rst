htmldate: find the publication date of web pages
================================================

.. image:: https://img.shields.io/pypi/v/htmldate.svg
    :target: https://pypi.python.org/pypi/htmldate
    :alt: Python package

.. image:: https://img.shields.io/pypi/pyversions/htmldate.svg
    :target: https://pypi.python.org/pypi/htmldate
    :alt: Python versions

.. image:: https://readthedocs.org/projects/htmldate/badge/?version=latest
    :target: https://htmldate.readthedocs.org/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/codecov/c/github/adbar/htmldate.svg
    :target: https://codecov.io/gh/adbar/htmldate
    :alt: Code Coverage

.. image:: https://static.pepy.tech/badge/htmldate/month
    :target: https://pepy.tech/project/htmldate
    :alt: Downloads

|

:Code:           https://github.com/adbar/htmldate
:Documentation:  https://htmldate.readthedocs.io
:Issue tracker:  https://github.com/adbar/htmldate/issues

|

.. image:: docs/htmldate-demo.gif
    :alt: Demo as GIF image
    :align: center
    :width: 85%
    :target: https://htmldate.readthedocs.org/

|

Find original and updated publication dates of any web page. From the command-line or within Python, all the steps needed from web page download to HTML parsing, scraping, and text analysis are included.

In a nutshell, with Python:

.. code-block:: python

    >>> from htmldate import find_date
    >>> find_date('http://blog.python.org/2016/12/python-360-is-now-available.html')
    '2016-12-23'
    >>> find_date('https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/', original_date=True)
    '2016-06-23'

On the command-line:

.. code-block:: bash

    $ htmldate -u http://blog.python.org/2016/12/python-360-is-now-available.html
    '2016-12-23'


Features
--------

*htmldate* finds original and updated publication dates of web pages using heuristics on HTML code and linguistic patterns. URLs, HTML files, or HTML trees are given as input. It provides following ways to date a HTML document:

1. **Markup in header**: common patterns are used to identify relevant elements (e.g. ``link`` and ``meta`` elements) including `Open Graph protocol <http://ogp.me/>`_ attributes and a large number of CMS idiosyncrasies
2. **HTML code**: The whole document is then searched for structural markers: ``abbr`` and ``time`` elements as well as a series of attributes (e.g. ``postmetadata``)
3. **Bare HTML content**: A series of heuristics is run on text and markup:

  - in ``fast`` mode the HTML page is cleaned and precise patterns are targeted
  - in ``extensive`` mode all potential dates are collected and a disambiguation algorithm determines the best one

The output is thouroughly verified in terms of plausibility and adequateness and the library outputs a date string, corresponding to either the last update or the original publishing statement (the default), in the desired format (defaults to `ISO 8601 YMD format <https://en.wikipedia.org/wiki/ISO_8601>`_).

-  Compatible with all recent versions of Python (currently 3.5 to 3.9)
-  Designed to be computationally efficient and used in production on millions of documents
-  Batch processing of a list of URLs
-  Switch between original and updated date

Markup-based extraction is multilingual by nature, text-based refinements for better coverage currently support German, English and Turkish.


Performance
-----------

=============================== ========= ========= ========= ========= =======
500 web pages containing identifiable dates (as of 2021-09-24)
-------------------------------------------------------------------------------
Python Package                  Precision Recall    Accuracy  F-Score   Time
=============================== ========= ========= ========= ========= =======
articleDateExtractor 0.20       0.769     0.691     0.572     0.728     3.3x
date_guesser 2.1.4              0.738     0.544     0.456     0.626     20x
goose3 3.1.9                    0.821     0.453     0.412     0.584     8.2x
htmldate[all] 0.9.1 (fast)      **0.839** 0.906     0.772     0.871     **1x**
htmldate[all] 0.9.1 (extensive) 0.825     **0.990** **0.818** **0.900** 1.7x
newspaper3k 0.2.8               0.729     0.630     0.510     0.675     8.4x
news-please 1.5.21              0.823     0.691     0.572     0.728     30x
=============================== ========= ========= ========= ========= =======

For complete results and explanations see the `evaluation page <https://htmldate.readthedocs.io/en/latest/evaluation.html>`_.


Installation
------------

This Python package is tested on Linux, macOS and Windows systems, it is compatible with Python 3.5 upwards. It is available on the package repository `PyPI <https://pypi.org/>`_ and can notably be installed with ``pip`` or ``pipenv``:

.. code-block:: bash

    $ pip install htmldate # pip3 install on systems where both Python 2 and 3 are installed
    $ pip install --upgrade htmldate # to make sure you have the latest version
    $ pip install git+https://github.com/adbar/htmldate.git # latest available code (see build status above)

Additional libraries can be installed to enhance efficiency: ``cchardet`` and ``ciso8601`` (for speed). They may not work on all platforms and have thus been singled out although installation is recommended:

.. code-block:: bash

    $ pip/pip3 install htmldate[speed] # install with additional functionality

You can also install or update the packages separately, *htmldate* will detect which ones are present on your system and opt for the best available combination.

*For infos on dependency management of Python packages see* `this discussion thread <https://stackoverflow.com/questions/41573587/what-is-the-difference-between-venv-pyvenv-pyenv-virtualenv-virtualenvwrappe>`_


With Python
-----------

.. code-block:: python

    >>> from htmldate import find_date
    >>> find_date('http://blog.python.org/2016/12/python-360-is-now-available.html')
    '2016-12-23'

Complete screening of the document with the ``extensive_search`` parameter:

.. code-block:: python

    >>> find_date('https://creativecommons.org/about/')
    '2017-08-11' # has been updated since
    >>> find_date('https://creativecommons.org/about/', extensive_search=False)
    >>>

Already parsed HTML (that is a LXML tree object):

.. code-block:: python

    # simple HTML document as string
    >>> htmldoc = '<html><body><span class="entry-date">July 12th, 2016</span></body></html>'
    >>> find_date(htmldoc)
    '2016-07-12'
    # parsed LXML tree
    >>> from lxml import html
    >>> mytree = html.fromstring('<html><body><span class="entry-date">July 12th, 2016</span></body></html>')
    >>> find_date(mytree)
    '2016-07-12'

Change the output to a format known to Python's ``datetime`` module, the default being ``%Y-%m-%d``:

.. code-block:: python

    >>> find_date('https://www.gnu.org/licenses/gpl-3.0.en.html', outputformat='%d %B %Y')
    '18 November 2016' # may have changed since

Although the time delta between original publication and "last modified" info is usually a matter of hours or days, it can be useful to prioritize the **original publication date**:

.. code-block:: python

    >>> find_date('https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/', original_date=True) # modified behavior
    '2016-06-23'


On the command-line
-------------------


.. code-block:: bash

    $ htmldate -u http://blog.python.org/2016/12/python-360-is-now-available.html
    '2016-12-23'
    $ htmldate --help
    htmldate [-h] [-v] [-f] [--original] [-min MINDATE] [-max MAXDATE] [-i INPUTFILE] [-u URL]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -f, --fast            fast mode: disable extensive search
  --original            original date prioritized
  -min, --mindate MINDATE
                        earliest acceptable date (YYYY-MM-DD)
  -max, --maxdate MAXDATE
                        latest acceptable date (YYYY-MM-DD)
  -i, --inputfile INPUTFILE
                        name of input file for batch processing (similar to
                        wget -i)
  -u, --URL URL     custom URL download

The batch mode ``-i`` takes one URL per line as input and returns one result per line in tab-separated format:

.. code-block:: bash

    $ htmldate --fast -i list-of-urls.txt


License
-------

*htmldate* is distributed under the `GNU General Public License v3.0 <https://github.com/adbar/htmldate/blob/master/LICENSE>`_. If you wish to redistribute this library but feel bounded by the license conditions please try interacting `at arms length <https://www.gnu.org/licenses/gpl-faq.html#GPLInProprietarySystem>`_, `multi-licensing <https://en.wikipedia.org/wiki/Multi-licensing>`_ with `compatible licenses <https://en.wikipedia.org/wiki/GNU_General_Public_License#Compatibility_and_multi-licensing>`_, or `contacting me <https://github.com/adbar/htmldate#author>`_.

See also `GPL and free software licensing: What's in it for business? <https://www.techrepublic.com/blog/cio-insights/gpl-and-free-software-licensing-whats-in-it-for-business/>`_


Going further
-------------

**Online documentation:** `htmldate.readthedocs.io <https://htmldate.readthedocs.io/>`_

If the date is nowhere to be found, it might be worth considering `carbon dating <https://github.com/oduwsdl/CarbonDate>`_ the web page, however this is computationally expensive. In addition, `datefinder <https://github.com/akoumjian/datefinder>`_ features pattern-based date extraction for texts written in English.


Author
------

This effort is part of methods to derive information from web documents in order to build `text databases for research <https://www.dwds.de/d/k-web>`_ (chiefly linguistic analysis and natural language processing). Extracting and pre-processing web texts to the exacting standards of scientific research presents a substantial challenge for those who conduct such research. There are web pages for which neither the URL nor the server response provide a reliable way to find out when a document was published or modified. For more information:

.. image:: https://joss.theoj.org/papers/10.21105/joss.02439/status.svg
   :target: https://doi.org/10.21105/joss.02439
   :alt: JOSS article

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.3459599.svg
   :target: https://doi.org/10.5281/zenodo.3459599
   :alt: Zenodo archive

-  Barbaresi, A. "`htmldate: A Python package to extract publication dates from web pages <https://doi.org/10.21105/joss.02439>`_", Journal of Open Source Software, 5(51), 2439, 2020.
-  Barbaresi, A. "`Generic Web Content Extraction with Open-Source Software <https://hal.archives-ouvertes.fr/hal-02447264/document>`_", Proceedings of KONVENS 2019, Kaleidoscope Abstracts, 2019.
-  Barbaresi, A. "`Efficient construction of metadata-enhanced web corpora <https://hal.archives-ouvertes.fr/hal-01371704v2/document>`_", Proceedings of the `10th Web as Corpus Workshop (WAC-X) <https://www.sigwac.org.uk/wiki/WAC-X>`_, 2016.

You can contact me via my `contact page <https://adrien.barbaresi.eu/>`_ or `GitHub <https://github.com/adbar>`_.


Contributing
------------

`Contributions <https://github.com/adbar/htmldate/blob/master/CONTRIBUTING.md>`_ are welcome!

Feel free to file issues on the `dedicated page <https://github.com/adbar/htmldate/issues>`_. Thanks to the `contributors <https://github.com/adbar/htmldate/graphs/contributors>`_ who submitted features and bugfixes!

Kudos to the following software libraries:

-  `ciso8601 <https://github.com/closeio/ciso8601>`_, `lxml <http://lxml.de/>`_, `dateparser <https://github.com/scrapinghub/dateparser>`_
-  A few patterns are derived from the `python-goose <https://github.com/grangier/python-goose>`_, `metascraper <https://github.com/ianstormtaylor/metascraper>`_, `newspaper <https://github.com/codelucas/newspaper>`_ and `articleDateExtractor <https://github.com/Webhose/article-date-extractor>`_ libraries. This module extends their coverage and robustness significantly.

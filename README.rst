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

.. image:: https://img.shields.io/pypi/dm/htmldate?color=informational
    :target: https://pepy.tech/project/htmldate
    :alt: Downloads

.. image:: https://img.shields.io/badge/JOSS-10.21105%2Fjoss.02439-brightgreen
   :target: https://doi.org/10.21105/joss.02439
   :alt: JOSS article reference DOI: 10.21105/joss.02439

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Code style: black

|

Find original and updated publication dates of any web page. From the command-line or within Python, all the steps needed from web page download to HTML parsing, scraping, and text analysis are included.

In a nutshell
-------------

|

.. image:: docs/htmldate-demo.gif
    :alt: Demo as GIF image
    :align: center
    :width: 80%
    :target: https://htmldate.readthedocs.org/

|

With Python:

.. code-block:: python

    >>> from htmldate import find_date
    >>> find_date('http://blog.python.org/2016/12/python-360-is-now-available.html')
    '2016-12-23'

On the command-line:

.. code-block:: bash

    $ htmldate -u http://blog.python.org/2016/12/python-360-is-now-available.html
    '2016-12-23'


Features
--------

-  Multilingual, robust and efficient (used in production on millions of documents)
-  URLs, HTML files, or HTML trees are given as input (includes batch processing)
-  Output as string in any date format (defaults to `ISO 8601 YMD <https://en.wikipedia.org/wiki/ISO_8601>`_)
-  Detection of both original and updated dates
-  Compatible with all recent versions of Python


``htmldate`` can examine markup and text. It provides the following ways to date an HTML document:

1. **Markup in header**: Common patterns are used to identify relevant elements (e.g. ``link`` and ``meta`` elements) including `Open Graph protocol <http://ogp.me/>`_ attributes
2. **HTML code**: The whole document is searched for structural markers: ``abbr`` or ``time`` elements and a series of attributes (e.g. ``postmetadata``)
3. **Bare HTML content**: Heuristics are run on text and markup:

  - in ``fast`` mode the HTML page is cleaned and precise patterns are targeted
  - in ``extensive`` mode all potential dates are collected and a disambiguation algorithm determines the best one

Finally the output is validated and converted to the chosen format.


Performance
-----------

=============================== ========= ========= ========= ========= =======
500 web pages containing identifiable dates (as of 2022-03-23 on Python 3.8)
-------------------------------------------------------------------------------
Python Package                  Precision Recall    Accuracy  F-Score   Time
=============================== ========= ========= ========= ========= =======
articleDateExtractor 0.20       0.769     0.691     0.572     0.728     4.4x
date_guesser 2.1.4              0.738     0.544     0.456     0.626     17x
goose3 3.1.11                   0.821     0.453     0.412     0.584     15x
htmldate[all] 1.2.1 (fast)      **0.848** 0.921     0.790     0.883     **1x**
htmldate[all] 1.2.1 (extensive) 0.839     **0.990** **0.832** **0.908** 2.3x
newspaper3k 0.2.8               0.729     0.630     0.510     0.675     12x
news-please 1.5.21              0.769     0.691     0.572     0.728     40x
=============================== ========= ========= ========= ========= =======

For complete results and explanations see the `evaluation page <https://htmldate.readthedocs.io/en/latest/evaluation.html>`_.


Installation
------------

This Python package is tested on Linux, macOS and Windows systems; it is compatible with Python 3.6 upwards. It is available on the package repository `PyPI <https://pypi.org/>`_ and can notably be installed with ``pip`` (``pip3`` where applicable): ``pip install htmldate`` and optionally ``pip install htmldate[speed]``.


Documentation
-------------

For more details on installation, Python & CLI usage, **please refer to the documentation**: `htmldate.readthedocs.io <https://htmldate.readthedocs.io/>`_


License
-------

*htmldate* is distributed under the `GNU General Public License v3.0 <https://github.com/adbar/htmldate/blob/master/LICENSE>`_. If you wish to redistribute this library but feel bounded by the license conditions please try interacting `at arms length <https://www.gnu.org/licenses/gpl-faq.html#GPLInProprietarySystem>`_, `multi-licensing <https://en.wikipedia.org/wiki/Multi-licensing>`_ with `compatible licenses <https://en.wikipedia.org/wiki/GNU_General_Public_License#Compatibility_and_multi-licensing>`_, or `contacting me <https://github.com/adbar/htmldate#author>`_.

See also `GPL and free software licensing: What's in it for business? <https://www.techrepublic.com/blog/cio-insights/gpl-and-free-software-licensing-whats-in-it-for-business/>`_


Author
------

This effort is part of methods to derive information from web documents in order to build `text databases for research <https://www.dwds.de/d/k-web>`_ (chiefly linguistic analysis and natural language processing). Extracting and pre-processing web texts to the exacting standards of scientific research presents a substantial challenge for those who conduct such research. There are web pages for which neither the URL nor the server response provide a reliable way to find out when a document was published or modified. For more information:

.. image:: https://img.shields.io/badge/JOSS-10.21105%2Fjoss.02439-brightgreen
   :target: https://doi.org/10.21105/joss.02439
   :alt: JOSS article reference DOI: 10.21105/joss.02439

.. image:: https://img.shields.io/badge/DOI-10.5281%2Fzenodo.3459599-blue
   :target: https://doi.org/10.5281/zenodo.3459599
   :alt: Zenodo archive DOI: 10.5281/zenodo.3459599


.. code-block:: shell

    @article{barbaresi-2020-htmldate,
      title = {{htmldate: A Python package to extract publication dates from web pages}},
      author = "Barbaresi, Adrien",
      journal = "Journal of Open Source Software",
      volume = 5,
      number = 51,
      pages = 2439,
      url = {https://doi.org/10.21105/joss.02439},
      publisher = {The Open Journal},
      year = 2020,
    }

-  Barbaresi, A. "`htmldate: A Python package to extract publication dates from web pages <https://doi.org/10.21105/joss.02439>`_", Journal of Open Source Software, 5(51), 2439, 2020. DOI: 10.21105/joss.02439
-  Barbaresi, A. "`Generic Web Content Extraction with Open-Source Software <https://hal.archives-ouvertes.fr/hal-02447264/document>`_", Proceedings of KONVENS 2019, Kaleidoscope Abstracts, 2019.
-  Barbaresi, A. "`Efficient construction of metadata-enhanced web corpora <https://hal.archives-ouvertes.fr/hal-01371704v2/document>`_", Proceedings of the `10th Web as Corpus Workshop (WAC-X) <https://www.sigwac.org.uk/wiki/WAC-X>`_, 2016.

You can contact me via my `contact page <https://adrien.barbaresi.eu/>`_ or `GitHub <https://github.com/adbar>`_.


Contributing
------------

`Contributions <https://github.com/adbar/htmldate/blob/master/CONTRIBUTING.md>`_ are welcome!

Feel free to file issues on the `dedicated page <https://github.com/adbar/htmldate/issues>`_. Thanks to the `contributors <https://github.com/adbar/htmldate/graphs/contributors>`_ who submitted features and bugfixes!

Kudos to the following software libraries:

-  `lxml <http://lxml.de/>`_, `dateparser <https://github.com/scrapinghub/dateparser>`_
-  A few patterns are derived from the `python-goose <https://github.com/grangier/python-goose>`_, `metascraper <https://github.com/ianstormtaylor/metascraper>`_, `newspaper <https://github.com/codelucas/newspaper>`_ and `articleDateExtractor <https://github.com/Webhose/article-date-extractor>`_ libraries. This module extends their coverage and robustness significantly.

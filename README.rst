Htmldate: Find the Publication Date of Web Pages
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

|


.. image:: https://raw.githubusercontent.com/adbar/htmldate/master/docs/htmldate-logo.png
    :alt: Logo as PNG image
    :align: center
    :width: 60%

|

Find **original and updated publication dates** of any web page. **On the command-line or with Python**, all the steps needed from web page download to HTML parsing, scraping, and text analysis are included. The package is used in production on millions of documents and integrated by `multiple libraries <https://github.com/adbar/htmldate/network/dependents>`_.


In a nutshell
-------------

|

.. image:: https://raw.githubusercontent.com/adbar/htmldate/master/docs/htmldate-demo.gif
    :alt: Demo as GIF image
    :align: center
    :width: 80%
    :target: https://htmldate.readthedocs.org/

|

With Python
~~~~~~~~~~~

.. code-block:: python

    >>> from htmldate import find_date
    >>> find_date('http://blog.python.org/2016/12/python-360-is-now-available.html')
    '2016-12-23'

On the command-line
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    $ htmldate -u http://blog.python.org/2016/12/python-360-is-now-available.html
    '2016-12-23'


Features
--------

- Flexible input: URLs, HTML files, or HTML trees can be used as input (including batch processing).
- Customizable output: Any date format (defaults to `ISO 8601 YMD <https://en.wikipedia.org/wiki/ISO_8601>`_).
- Detection of both original and updated dates.
- Multilingual.
- Compatible with all recent versions of Python.


How it works
~~~~~~~~~~~~

Htmldate operates by sifting through HTML markup and if necessary text elements. It features the following heuristics:

1. **Markup in header**: Common patterns are used to identify relevant elements (e.g. ``link`` and ``meta`` elements) including `Open Graph protocol <http://ogp.me/>`_ attributes.
2. **HTML code**: The whole document is searched for structural markers like ``abbr`` or ``time`` elements and a series of attributes (e.g. ``postmetadata``).
3. **Bare HTML content**: Heuristics are run on text and markup:
   - In ``fast`` mode the HTML page is cleaned and precise patterns are targeted.
   - In ``extensive`` mode all potential dates are collected and a disambiguation algorithm determines the best one.


Finally, the output is validated and converted to the chosen format.


Performance
-----------

=============================== ========= ========= ========= ========= =======
1000 web pages containing identifiable dates (as of 2023-11-13 on Python 3.10)
-------------------------------------------------------------------------------
Python Package                  Precision Recall    Accuracy  F-Score   Time
=============================== ========= ========= ========= ========= =======
articleDateExtractor 0.20       0.803     0.734     0.622     0.767     5x
date_guesser 2.1.4              0.781     0.600     0.514     0.679     18x
goose3 3.1.17                   0.869     0.532     0.493     0.660     15x
htmldate[all] 1.6.0 (fast)      **0.883** 0.924     0.823     0.903     **1x**
htmldate[all] 1.6.0 (extensive) 0.870     **0.993** **0.865** **0.928** 1.7x
newspaper3k 0.2.8               0.769     0.667     0.556     0.715     15x
news-please 1.5.35              0.801     0.768     0.645     0.784     34x
=============================== ========= ========= ========= ========= =======

For the complete results and explanations see `evaluation page <https://htmldate.readthedocs.io/en/latest/evaluation.html>`_.


Installation
------------

Htmldate is tested on Linux, macOS and Windows systems, it is compatible with Python 3.6 upwards. It can notably be installed with ``pip`` (``pip3`` where applicable) from the PyPI package repository:  

-  ``pip install htmldate`` 
-  (optionally) ``pip install htmldate[speed]``


Documentation
-------------

For more details on installation, Python & CLI usage, **please refer to the documentation**: `htmldate.readthedocs.io <https://htmldate.readthedocs.io/>`_


License
-------

This package is distributed under the `GNU General Public License v3.0 <https://github.com/adbar/htmldate/blob/master/LICENSE>`_. If you wish to redistribute this library but feel bounded by the license conditions please try interacting `at arms length <https://www.gnu.org/licenses/gpl-faq.html#GPLInProprietarySystem>`_, `multi-licensing <https://en.wikipedia.org/wiki/Multi-licensing>`_ with `compatible licenses <https://en.wikipedia.org/wiki/GNU_General_Public_License#Compatibility_and_multi-licensing>`_, or `contacting me <https://github.com/adbar/htmldate#author>`_.

See also `GPL and free software licensing: What's in it for business? <https://www.techrepublic.com/blog/cio-insights/gpl-and-free-software-licensing-whats-in-it-for-business/>`_


Author
------

This project is part of methods to derive information from web documents in order to build `text databases for research <https://www.dwds.de/d/k-web>`_ (chiefly linguistic analysis and natural language processing).

Extracting and pre-processing web texts to meet the exacting standards is a significant challenge. It is often not possible to reliably determine the date of publication or modification using either the URL or the server response. For more information:

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

`Contributions <https://github.com/adbar/htmldate/blob/master/CONTRIBUTING.md>`_ are welcome as well as issues filed on the `dedicated page <https://github.com/adbar/htmldate/issues>`_.

Special thanks to the `contributors <https://github.com/adbar/htmldate/graphs/contributors>`_ who have submitted features and bugfixes!


Acknowledgements
----------------

Kudos to the following software libraries:

-  `lxml <http://lxml.de/>`_, `dateparser <https://github.com/scrapinghub/dateparser>`_
-  A few patterns are derived from the `python-goose <https://github.com/grangier/python-goose>`_, `metascraper <https://github.com/ianstormtaylor/metascraper>`_, `newspaper <https://github.com/codelucas/newspaper>`_ and `articleDateExtractor <https://github.com/Webhose/article-date-extractor>`_ libraries. This module extends their coverage and robustness significantly.

htmldate: find the publication date of web pages
================================================

.. image:: https://img.shields.io/pypi/v/htmldate.svg
    :target: https://pypi.python.org/pypi/htmldate
    :alt: Python package

.. image:: https://img.shields.io/pypi/pyversions/htmldate.svg
    :target: https://pypi.python.org/pypi/htmldate
    :alt: Python versions

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

.. image:: htmldate-logo.png
    :alt: Logo as PNG image
    :align: center
    :width: 60%

|

Find original and updated publication dates of any web page. From the command-line or within Python, all the steps needed from web page download to HTML parsing, scraping, and text analysis are included.


In a nutshell
-------------

|

.. image:: htmldate-demo.gif
    :alt: Demo as GIF image
    :align: center
    :width: 95%
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

1. **Markup in header**: Common patterns are used to identify relevant elements (e.g. ``link`` and ``meta`` elements) including `Open Graph protocol <http://ogp.me/>`_ attributes and a large number of CMS idiosyncrasies
2. **HTML code**: The whole document is then searched for structural markers: ``abbr`` or ``time`` elements and a series of attributes (e.g. ``postmetadata``)
3. **Bare HTML content**: Heuristics are run on text and markup:

  - in ``fast`` mode the HTML page is cleaned and precise patterns are targeted
  - in ``extensive`` mode all potential dates are collected and a disambiguation algorithm determines the most probable one

The output is thoroughly verified in terms of plausibility and adequateness. If a valid date has been found the library outputs a date string corresponding to either the last update or the original publishing statement (the default), in the desired format.

Markup-based extraction is multilingual by nature, text-based refinements for better coverage currently support German, English and Turkish.


Installation
------------

Main package
~~~~~~~~~~~~

This Python package is tested on Linux, macOS and Windows systems; it is compatible with Python 3.6 upwards. It is available on the package repository `PyPI <https://pypi.org/>`_ and can notably be installed with ``pip`` or ``pipenv``:

.. code-block:: bash

    $ pip install htmldate # pip3 install on systems where both Python 2 and 3 are installed
    $ pip install --upgrade htmldate # to make sure you have the latest version
    $ pip install git+https://github.com/adbar/htmldate.git # latest available code (see build status above)


Optional
~~~~~~~~

The additional library ``cchardet`` (or its fork ``faust-cchardet``) can be installed for better execution speed. They may not work on all platforms and have thus been singled out although installation is recommended:

.. code-block:: bash

    $ pip install htmldate[speed] # install with additional functionality

You can also install or update the packages separately, *htmldate* will detect which ones are present on your system and opt for the best available combination.

The ``dateparser`` package is noticeably slower in its latest versions, version ``1.1.2`` is recommended for speed.

*For infos on dependency management of Python packages see* `this discussion thread <https://stackoverflow.com/questions/41573587/what-is-the-difference-between-venv-pyvenv-pyenv-virtualenv-virtualenvwrappe>`_.


Experimental
~~~~~~~~~~~~

Experimental compilation with ``mypyc``, as using pre-compiled library may shorten processing speed:

1. Install ``mypy``: ``pip3 install mypy``
2. Compile the package: ``python setup.py --use-mypyc bdist_wheel``
3. Use the newly created wheel: ``pip3 install dist/...``


With Python
-----------

``find_date``
~~~~~~~~~~~~~

In case the web page features easily readable metadata in the header, the extraction is straightforward. A more advanced analysis of the document structure is sometimes needed:

.. code-block:: python

    >>> from htmldate import find_date
    >>> find_date('http://blog.python.org/2016/12/python-360-is-now-available.html')
    # DEBUG analyzing: <h2 class="date-header"><span>Friday, December 23, 2016</span></h2>
    # DEBUG result: 2016-12-23
    '2016-12-23'

``htmldate`` can resort to a guess based on a complete screening of the document (``extensive_search`` parameter) which can be deactivated:

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


Output format
~~~~~~~~~~~~~

Change the output to a format known to Python's ``datetime`` module, the default being ``%Y-%m-%d``:

.. code-block:: python

    >>> find_date('https://www.gnu.org/licenses/gpl-3.0.en.html', outputformat='%d %B %Y')
    '18 November 2016'  # may have changed since


Original vs. updated dates
~~~~~~~~~~~~~~~~~~~~~~~~~~

Although the time delta between original publication and "last modified" info is usually a matter of hours or days, it can be useful to prioritize the **original publication date**:

.. code-block:: python

    >>> find_date('https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/', original_date=True)  # modified behavior
    '2016-06-23'

For more information see `options page <options.html>`_.


On the command-line
-------------------

A command-line interface is included:

.. code-block:: bash

    $ htmldate -u http://blog.python.org/2016/12/python-360-is-now-available.html
    '2016-12-23'
    $ wget -qO- "http://blog.python.org/2016/12/python-360-is-now-available.html" | htmldate
    '2016-12-23'

For usage instructions see ``htmldate -h``:

.. code-block:: bash

    $ htmldate --help
    htmldate [-h] [-f] [-i INPUTFILE] [--original] [-min MINDATE] [-max MAXDATE] [-u URL] [-v] [--version]
    optional arguments:
        -h, --help            show this help message and exit
        -f, --fast            fast mode: disable extensive search
        -i INPUTFILE, --inputfile INPUTFILE
                              name of input file for batch processing (similar to wget -i)
        --original            original date prioritized
        -min MINDATE, --mindate MINDATE
                              earliest acceptable date (YYYY-MM-DD)
        -max MAXDATE, --maxdate MAXDATE
                              latest acceptable date (YYYY-MM-DD)
        -u URL, --URL URL     custom URL download
        -v, --verbose         increase output verbosity
        --version             show version information and exit


The batch mode ``-i`` takes one URL per line as input and returns one result per line in tab-separated format:

.. code-block:: bash

    $ htmldate --fast -i list-of-urls.txt


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


Going further
-------------

Known caveats
~~~~~~~~~~~~~

The granularity may not always match the desired output format. If only information about the year could be found and the chosen date format requires to output a month and a day, the result is 'padded' to be located at the middle of the year, in that case the 1st of January.

Besides, there are pages for which no date can be found, ever:

.. code-block:: python

    >>> r = requests.get('https://example.com')
    >>> htmldate.find_date(r.text)
    >>>

If the date is nowhere to be found, it might be worth considering `carbon dating <https://github.com/oduwsdl/CarbonDate>`_ the web page, however this is computationally expensive. In addition, `datefinder <https://github.com/akoumjian/datefinder>`_ features pattern-based date extraction for texts written in English.


.. toctree::
   :maxdepth: 2

   corefunctions
   evaluation
   options
   used-by


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

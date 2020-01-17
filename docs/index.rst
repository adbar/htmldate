htmldate: find the publication date of web pages
================================================

.. image:: https://img.shields.io/pypi/v/htmldate.svg
    :target: https://pypi.python.org/pypi/htmldate
    :alt: Python package

.. image:: https://img.shields.io/pypi/l/htmldate.svg
    :target: https://pypi.python.org/pypi/htmldate
    :alt: License

.. image:: https://img.shields.io/pypi/pyversions/htmldate.svg
    :target: https://pypi.python.org/pypi/htmldate
    :alt: Python versions

.. image:: https://readthedocs.org/projects/htmldate/badge/?version=latest
    :target: http://htmldate.readthedocs.org/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/travis/adbar/htmldate.svg
    :target: https://travis-ci.org/adbar/htmldate
    :alt: Travis build status

.. image:: https://img.shields.io/appveyor/ci/adbar/htmldate
    :target: https://ci.appveyor.com/project/adbar/htmldate
    :alt: Appveyor/Windows build status

.. image:: https://img.shields.io/codecov/c/github/adbar/htmldate.svg
    :target: https://codecov.io/gh/adbar/htmldate
    :alt: Code Coverage

|

:Code:           https://github.com/adbar/htmldate
:Documentation:  https://htmldate.readthedocs.io
:Issue tracker:  https://github.com/adbar/htmldate/issues

|

.. image:: htmldate-demo.gif
    :alt: Demo as GIF image
    :align: center
    :width: 85%
    :target: https://htmldate.readthedocs.org/

|

*htmldate* finds original and updated publication dates of any web page. All the steps needed from web page download to HTML parsing, scraping and text analysis are included. URLs, HTML files or HTML trees are given as input, the library outputs a date string in the desired format.

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

|

.. contents:: **Contents**
    :backlinks: none

|

Features
--------

The library uses a combination of tree traversal, common structural patterns, text-based heuristics and robust date extraction. It provides following ways to date a HTML document:

1. **Markup in header**: common patterns are used to identify relevant elements (e.g. ``link`` and ``meta`` elements) including `Open Graph protocol <http://ogp.me/>`_ attributes and a large number of CMS idiosyncracies
2. **HTML code**: The whole document is then searched for structural markers: ``abbr``/``time`` elements and a series of attributes (e.g. ``postmetadata``)
3. **Bare HTML content**: A series of heuristics is run on text and markup:

  1. in ``fast`` mode the HTML page is cleaned and precise patterns are targeted
  2. in ``extensive`` mode all potential dates are collected and disambiguation algorithm determines the best one

The module returns a date if a valid cue could be found in the document, corresponding to either the last update (default) or the original publishing statement. The output string defaults to `ISO 8601 YMD format <https://en.wikipedia.org/wiki/ISO_8601>`_.

-  Should be compatible with all common versions of Python 3 (see tests and coverage)
-  Safety belt included, utput thouroughly verified in terms of plausibility and adequateness
-  Designed to be computationally efficient and used in production on millions of documents
-  Batch processing of a list of URLs
-  Switch between original and updated date


Installation
------------

This Python package is tested on Linux, macOS and Windows systems, it is compatible with Python 3.4 upwards. It is available on the package repository `PyPI <https://pypi.org/>`_ and can notably be installed with ``pip`` or ``pipenv``:

.. code-block:: bash

    $ pip install htmldate # pip3 install on systems where both Python 2 and 3 are installed
    $ pip install --upgrade htmldate # to make sure you have the latest version
    $ pip install git+https://github.com/adbar/htmldate.git # latest available code (see build status above)

A few additional libraries can be installed to enhance coverage and speed, most importantly ``ciso8601`` and ``regex`` (for speed) as well as ``dateparser`` (to go beyond the current focus on English or German). They may not work on all platforms and have thus been singled out although installation is recommended:

.. code-block:: bash

    $ pip install htmldate[all] # install with all additional functionality

You can also install or update the packages separately, *htmldate* will detect which ones are present on your system and opt for the best available combination.

For faster processing of downloads you may also consider installing the ``cchardet`` package as well (currently not working on some macOS versions).

*For infos on dependency management of Python packages see* `this discussion thread <https://stackoverflow.com/questions/41573587/what-is-the-difference-between-venv-pyvenv-pyenv-virtualenv-virtualenvwrappe>`_


With Python
-----------

All the functions of the module are currently bundled in *htmldate*.

In case the web page features easily readable metadata in the header, the extraction is straightforward. A more advanced analysis of the document structure is sometimes needed:

.. code-block:: python

    >>> from htmldate import find_date
    >>> find_date('http://blog.python.org/2016/12/python-360-is-now-available.html')
    '# DEBUG analyzing: <h2 class="date-header"><span>Friday, December 23, 2016</span></h2>'
    '# DEBUG result: 2016-12-23'
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
    >>> find_date(mytree)
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

    >>> find_date('https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/') # default setting
    '2019-06-24'
    >>> find_date('https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/', original_date=True) # modified behavior
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
    htmldate [-h] [-v] [-f] [--original] [-m MAXDATE] [-i INPUTFILE] [-u URL]
    optional arguments:
        -h, --help     show this help message and exit
        -v, --verbose  increase output verbosity
        -f, --fast     fast mode: disable extensive search
        --original     original date prioritized
        -m MAXDATE, --maxdate MAXDATE
                       latest acceptable date (YYYY-MM-DD)
        -i INPUTFILE, --inputfile INPUTFILE
                       name of input file for batch processing (similar to
                       wget -i)
        -u URL, --URL URL     custom URL download

The batch mode ``-i`` takes one URL per line as input and returns one result per line in tab-separated format:

.. code-block:: bash

    $ htmldate --fast -i list-of-urls.txt


License
-------

*htmldate* is distributed under the `GNU General Public License v3.0 <https://github.com/adbar/htmldate/blob/master/LICENSE>`_

`GPL and free software licensing: What's in it for business? <https://www.techrepublic.com/blog/cio-insights/gpl-and-free-software-licensing-whats-in-it-for-business/>`_


Author
------

This effort is part of methods to derive information from web documents in order to build text databases for research (chiefly linguistics and natural language processing). There are web pages for which neither the URL nor the server response provide a reliable way to find when a document was published or modified. For more information:

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.3459599.svg
   :target: https://doi.org/10.5281/zenodo.3459599

-  Barbaresi, A. "`Generic Web Content Extraction with Open-Source Software <https://konvens.org/proceedings/2019/papers/kaleidoskop/camera_ready_barbaresi.pdf>`_", Proceedings of KONVENS 2019, Kaleidoscope Abstracts, 2019.
-  Barbaresi, A. "`Efficient construction of metadata-enhanced web corpora <https://hal.archives-ouvertes.fr/hal-01371704v2/document>`_", Proceedings of the `10th Web as Corpus Workshop (WAC-X) <https://www.sigwac.org.uk/wiki/WAC-X>`_, 2016.

You can contact me via my `contact page <http://adrien.barbaresi.eu/contact.html>`_ or `GitHub <https://github.com/adbar>`_.


Contributing
------------

Thanks to these contributors who submitted features and bugfixes:

-  `DerKozmonaut <https://github.com/DerKozmonaut>`_
-  `vbarbaresi <https://github.com/vbarbaresi>`_

`Contributions <https://github.com/adbar/htmldate/blob/master/CONTRIBUTING.md>`_ are welcome!

Feel free to file bug reports on the `issues page <https://github.com/adbar/htmldate/issues>`_.

Kudos to the following software libraries:

-  `cchardet <https://github.com/PyYoshi/cChardet>`_, `ciso8601 <https://github.com/closeio/ciso8601>`_, `lxml <http://lxml.de/>`_, `dateparser <https://github.com/scrapinghub/dateparser>`_
-  A few patterns are derived from `python-goose <https://github.com/grangier/python-goose>`_, `metascraper <https://github.com/ianstormtaylor/metascraper>`_, `newspaper <https://github.com/codelucas/newspaper>`_ and `articleDateExtractor <https://github.com/Webhose/article-date-extractor>`_. This module extends their coverage and robustness significantly.


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

In addition, `datefinder <https://github.com/akoumjian/datefinder>`_ features pattern-based date extraction for texts written in English.

Tests
~~~~~

A series of webpages triggering different structural and content patterns is included for testing purposes:

.. code-block:: bash

    $ pytest tests/unit_tests.py


.. toctree::
   :maxdepth: 2

   corefunctions
   options


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Options
=======

All options are parameters of ``find_date``, most of them also exist on the command-line.


Overview
--------

.. list-table::
   :header-rows: 1
   :widths: 25 20 15 40

   * - Parameter
     - Default
     - Command-line
     - Effect
   * - ``extensive_search``
     - ``True``
     - ``-f``, ``--fast`` to disable
     - Search the whole text if markup gives no date
   * - ``original_date``
     - ``False``
     - ``--original``
     - Prefer the original publication date to the last update
   * - ``outputformat``
     - ``"%Y-%m-%d"``
     -
     - Format of the returned string
   * - ``min_date``
     - ``1995-01-01``
     - ``-min``, ``--mindate``
     - Earliest acceptable date
   * - ``max_date``
     - end of the current day
     - ``-max``, ``--maxdate``
     - Latest acceptable date
   * - ``url``
     - canonical link if present
     -
     - URL searched for a date
   * - ``deferred_url_extractor``
     - ``False``
     -
     - Try the URL date only after the header markup and JSON-LD
   * - ``verbose``
     - ``False``
     - ``-v``, ``--verbose``
     - Print debug logs


Input
-----

``find_date`` accepts an HTML document as a string or as bytes, an already parsed LXML tree, or a URL.
A string starting with ``http`` and without spaces is treated as a URL and downloaded.

.. code-block:: python

    >>> from htmldate import find_date
    >>> htmldoc = '<html><body><span class="entry-date">July 12th, 2016</span></body></html>'
    >>> find_date(htmldoc)
    '2016-07-12'
    >>> find_date(htmldoc.encode("utf-8"))
    '2016-07-12'
    >>> from lxml import html
    >>> find_date(html.fromstring(htmldoc))
    '2016-07-12'

Passing a tree avoids parsing the same document twice when it is processed by other tools as well.
The tree is copied before cleaning, so it is not modified.

The download can also be done separately, with htmldate's own ``fetch_url`` function or with another library:

.. code-block:: python

    >>> from htmldate.utils import fetch_url
    >>> htmldoc = fetch_url('https://blog.wikimedia.org/2018/06/28/interactive-maps-now-in-your-language/')
    >>> find_date(htmldoc)
    '2018-06-28' # may change
    >>> import requests
    >>> r = requests.get('https://www.gov.uk/government/publications/open-standards-principles')
    >>> find_date(r.text)
    '2018-04-05' # may change


Extensive and fast modes
------------------------

By default, ``htmldate`` resorts to a guess based on a complete screening of the document if markup gives no result.
The fast mode skips this step: it outputs fewer dates but they are more often correct.

.. code-block:: python

    >>> find_date('https://www.bfs.de/SharedDocs/Pressemitteilungen/BfS/DE/2022/001.html')
    '2022-01-25'
    >>> find_date('https://www.bfs.de/SharedDocs/Pressemitteilungen/BfS/DE/2022/001.html', extensive_search=False)
    >>>

Both modes read dates in markup.
In date elements, both recognize month names in English, French, German, Indonesian, Polish, Russian and Turkish, as well as year-month-day forms in Chinese, Japanese and Korean.
Only the extensive mode reads dates in the running text.
It also uses `dateparser <https://github.com/scrapinghub/dateparser>`_ and thus recognizes further languages such as Spanish, Italian, Dutch or Portuguese.


Original date
-------------

Although the time delta between the original publication and the "last modified" statement is usually a matter of hours or days at most, it can be useful in some contexts to prioritize the original publication date during extraction:

.. code-block:: python

    >>> find_date('https://www.gov.uk/government/publications/open-standards-principles') # default setting
    '2018-04-05' # may change
    >>> find_date('https://www.gov.uk/government/publications/open-standards-principles', original_date=True) # modified behavior
    '2013-04-09'


Output format
-------------

Change the output to a format known to Python's ``datetime`` module, the default being ``%Y-%m-%d``:

.. code-block:: python

    >>> find_date('https://www.gov.uk/government/publications/open-standards-principles', outputformat='%d %B %Y')
    '05 April 2018' # may change
    >>> find_date('https://www.gov.uk/government/publications/open-standards-principles', outputformat='%Y-%m-%dT%H:%M:%S%z')
    '2018-04-05T10:46:37+0100' # may change

The time and the timezone are only known if the page provides them.
Otherwise the time is ``00:00:00`` and ``%z`` gives an empty string.

If only a year or a month could be found, the result is padded to the first day of the year or month: ``2017`` becomes ``2017-01-01`` and ``03/2017`` becomes ``2017-03-01``.

An invalid format makes ``find_date`` return ``None``:

.. autofunction:: htmldate.validators.is_valid_format


Date bounds
-----------

Dates outside of the range defined by ``min_date`` and ``max_date`` are discarded.
Both take a ``datetime`` object or a string in ISO 8601 format.
By default, dates before 1995 and after the end of the current day are ignored.

.. code-block:: python

    >>> htmldoc = '<html><head><meta name="date" content="1990-05-01"></head></html>'
    >>> find_date(htmldoc)
    >>> find_date(htmldoc, min_date='1980-01-01')
    '1990-05-01'

On the command-line, use ``--mindate`` and ``--maxdate`` with dates in ``YYYY-MM-DD`` format.


URL
---

A complete date in the URL (year, month and day) is used first, it is often reliable and much faster to extract.
If the ``url`` parameter is not set, the canonical link of the page (``<link rel="canonical">``) is used if present.

.. code-block:: python

    >>> find_date('<html><body></body></html>', url='https://example.org/2021/03/15/post')
    '2021-03-15'

With ``deferred_url_extractor=True``, the date in the URL is only used if the header markup and the JSON-LD data give no result.
This favors more precise expressions, for example a full timestamp in the metadata.


Return values and errors
------------------------

``find_date`` returns a string, or ``None`` if no valid date is found or if the output format is invalid.

It raises a ``ValueError`` if a URL given as input cannot be downloaded, and a ``TypeError`` for unsupported input types:

.. code-block:: python

    >>> try:
    ...     result = find_date(url)
    ... except ValueError:
    ...     result = None  # download failed

On the command-line, nothing is written to standard output if no date is found, errors go to standard error.
In batch mode, the result is written as ``None`` on the line of the URL.


Logging
-------

``verbose=True`` calls ``logging.basicConfig`` with the ``DEBUG`` level to show each step of the extraction.
In an application with its own logging configuration, raise the level of the ``htmldate`` logger only:

.. code-block:: python

    >>> import logging
    >>> logging.basicConfig(level=logging.WARNING)
    >>> logging.getLogger("htmldate").setLevel(logging.DEBUG)


Clearing caches
---------------

Date parsing results are kept in memory caches to speed up processing of many documents.
In long-running processes, clearing them from time to time releases memory:

.. code-block:: python

    >>> from htmldate.meta import reset_caches
    >>> reset_caches()


Settings
--------

The values in ``settings.py`` are read when the package is imported, assigning new values afterwards has no effect.
They are listed here for reference.
Use ``min_date`` and ``max_date`` to change the date range.

.. automodule:: htmldate.settings
   :members:
   :undoc-members:


Tests
-----

A series of HTML pages and patterns triggering different structural and content patterns is included for testing purposes.
Most tests run on saved pages, a few of them need a network connection.
From a clone of the repository:

.. code-block:: bash

    $ pip install -e ".[dev]"
    $ pytest

To run the evaluation, see the `evaluation page <evaluation.html>`_.

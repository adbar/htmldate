Options
=======

Configuration
-------------


Input format
~~~~~~~~~~~~

The module expects strings as shown above, it is also possible to use already parsed HTML (i.e. a LXML tree object):

.. code-block:: python

    >>> from htmldate import find_date
    >>> from lxml import html
    >>> mytree = html.fromstring('<html><body><span class="entry-date">July 12th, 2016</span></body></html>')
    >>> find_date(mytree)
    '2016-07-12'

An external module can be used for download, as described in versions anterior to 0.3. This example uses the legacy mode with `requests <http://docs.python-requests.org/>`_ as external module.

.. code-block:: python

    >>> from htmldate.core import find_date
    # using requests
    >>> import requests
    >>> r = requests.get('https://creativecommons.org/about/')
    >>> find_date(r.text)
    '2017-11-28' # may have changed since
    # using htmldate's own fetch_url function
    >>> from htmldate.utils import fetch_url
    >>> htmldoc = fetch_url('https://blog.wikimedia.org/2018/06/28/interactive-maps-now-in-your-language/')
    >>> find_date(htmldoc)
    '2018-06-28'
    # or simply
    >>> find_date('https://blog.wikimedia.org/2018/06/28/interactive-maps-now-in-your-language/') # URL detected
    '2018-06-28'


Date format
~~~~~~~~~~~

Change the output to a format known to Python's ``datetime`` module, the default being ``%Y-%m-%d``:

.. code-block:: python

    >>> find_date('https://www.gnu.org/licenses/gpl-3.0.en.html', outputformat='%d %B %Y')
    '18 November 2016' # may have changed since
    >>> find_date('http://blog.python.org/2016/12/python-360-is-now-available.html', outputformat='%Y-%m-%dT%H:%M:%S%z')
    '2016-12-23T05:11:00-0500'


.. autofunction:: htmldate.validators.output_format_validator


Original date
~~~~~~~~~~~~~

Although the time delta between the original publication and the "last modified" statement is usually a matter of hours or days at most, it can be useful in some contexts to prioritize the original publication date during extraction:

.. code-block:: python

    >>> find_date('https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/') # default setting
    '2019-06-24'
    >>> find_date('https://netzpolitik.org/2016/die-cider-connection-abmahnungen-gegen-nutzer-von-creative-commons-bildern/', original_date=True) # modified behavior
    '2016-06-23'


Settings
--------

See ``settings.py`` file:

.. automodule:: htmldate.settings
   :members:
   :show-inheritance:
   :undoc-members:

The module can then be re-compiled locally to apply changes to the settings.


Clearing caches
~~~~~~~~~~~~~~~

.. code-block:: python

    >>> from htmldate.meta import reset_caches
    # at a given point in time
    >>> reset_caches()

*New in version 1.3.0.*


Tests
-----

A series of HTML pages and patterns triggering different structural and content patterns is included for testing purposes:

.. code-block:: bash

    $ python3 -m pip install pytest
    $ pytest

Core functions
==============


Main function
-------------

.. autofunction:: htmldate.core.find_date

See the `options page <options.html>`_ for examples of each parameter.


Internal functions
------------------

These functions are not part of the public interface and may change between versions.
They return a ``datetime`` or ``None``: only ``find_date`` applies the output format.
Most of them take the extraction options as an ``Extractor`` object.

.. autoclass:: htmldate.utils.Extractor

.. autofunction:: htmldate.core.examine_header

.. autofunction:: htmldate.core.search_page

.. autofunction:: htmldate.extractors.try_date_expr

.. autofunction:: htmldate.extractors.custom_parse

.. autofunction:: htmldate.extractors.regex_parse

.. autofunction:: htmldate.extractors.extract_url_date

.. autofunction:: htmldate.extractors.external_date_parser


Helpers
-------

.. autofunction:: htmldate.validators.validate

.. autofunction:: htmldate.utils.load_html

.. autofunction:: htmldate.utils.fetch_url

.. autofunction:: htmldate.meta.reset_caches

Core functions
==============

.. contents:: **Contents**
    :backlinks: none


Handling date extraction
------------------------

.. autofunction:: htmldate.core.find_date

.. autofunction:: htmldate.core.examine_header

.. autofunction:: htmldate.core.search_page


Useful internal functions
-------------------------

Internal functions return a ``datetime`` or ``None``: only ``find_date`` applies the output format.

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

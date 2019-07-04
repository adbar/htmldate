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

.. autofunction:: htmldate.core.try_ymd_date

.. autofunction:: htmldate.parsers.custom_parse

.. autofunction:: htmldate.parsers.regex_parse_de

.. autofunction:: htmldate.parsers.regex_parse_en

.. autofunction:: htmldate.parsers.extract_url_date

.. autofunction:: htmldate.parsers.extract_partial_url_date

.. autofunction:: htmldate.parsers.external_date_parser


Helpers
-------

.. autofunction:: htmldate.parsers.convert_date

.. autofunction:: htmldate.parsers.date_validator

.. autofunction:: htmldate.utils.load_html

.. autofunction:: htmldate.utils.fetch_url

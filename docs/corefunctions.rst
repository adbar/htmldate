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

.. autofunction:: htmldate.extractors.custom_parse

.. autofunction:: htmldate.extractors.regex_parse_de

.. autofunction:: htmldate.extractors.regex_parse_en

.. autofunction:: htmldate.extractors.extract_url_date

.. autofunction:: htmldate.extractors.extract_partial_url_date

.. autofunction:: htmldate.extractors.external_date_parser


Helpers
-------

.. autofunction:: htmldate.extractors.convert_date

.. autofunction:: htmldate.extractors.date_validator

.. autofunction:: htmldate.utils.load_html

.. autofunction:: htmldate.utils.fetch_url

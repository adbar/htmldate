---
title: 'htmldate: A Python package to extract publication dates from web pages'
tags:
  - Python
  - metadata extraction
  - date parsing
  - web scraping
  - natural language processing
authors:
  - name: Adrien Barbaresi
    orcid: 0000-0002-8079-8694
    affiliation: Berlin-Brandenburg Academy of Sciences
date: 25 March 2020
bibliography: paper.bib
---



# Introduction


Although text is ubiquitous on the Web, extracting information from web pages can prove to be difficult. Web documents come in different shapes and sizes mostly because of the wide variety of genres, platforms or content management systems, and not least because of diverging publication goals. As a consequence, substantial filtering and quality assessment based on the purpose of data collection are crucial.

Metadata extraction is useful for purposes ranging from knowledge extraction and business intelligence to classification and refined visualizations. The date is a critical component, since it is one of the few metadata that are relevant both from a philological standpoint and in the context of information extraction for use in digital databases. It is often necessary to fully parse the document or apply robust scraping patterns, there are for example webpages for which neither the URL nor the server response provide a reliable way to date the document, that is find when it was written or modified. Being able to better qualify content allows for insights based on metadata (e.g. content type, authors or categories), better bandwidth control (e.g. by knowing when webpages have been updated), or optimization of indexing (e.g. language-based heuristics, LRU cache, etc.).

Large "offline" web text collections are now standard among the research community in linguistics and natural language processing. The construction of such text corpora notably involves "crawling, downloading, 'cleaning' and de-duplicating the data, then linguistically annotating it and loading it into a corpus query tool." [@Kilgarriff:2007] Web crawling [@Olston:2010] involves a significant number of design decisions and turning points in data processing, without which data and applications turn into a "wild West" [@JoGebru:2020]. Corresponding to the potential lack of metadata gathered with or obtained from the document, there is a lack of information regarding the content, whose adequacy, focus and quality are the object of a post hoc evaluation [@Baroni:2009]. Between opportunistic and restrained data collection [@Barbaresi:2015], a significant challenge lies in the ability to extract and pre-process web data to meet scientific expectations with respect to corpus quality.


## Rationale

This effort is part of a methodological approach to derive information from web documents in order to build text databases for research (chiefly linguistics and natural language processing). There are web pages for which neither the URL nor the server response provide a reliable way to find out when a document was published or modified. Improving the extraction methods for web collections can hopefully allow for combining both the quantity resulting from broad web crawling and the quality obtained by carefully extracting text and metadata and by rejecting documents that do not match certain criteria.

Fellow colleagues are working on a lexicographic information platform [@GeykenEtAl:2017] at the language center of the Berlin-Brandenburg Academy of Sciences ((dwds.de)[https://www.dwds.de/]), with hosts a series of metadata-enhanced web corpora [@Barbaresi:2016]. Information on publication and modification dates is crucial to be able to determine with precision when a given word has been used for the first time and how its use evolves through time.


# Functionality


``htmldate`` finds original and updated publication dates of web pages using heuristics on HTML code and linguistic patterns. URLs, HTML files or HTML trees are given as input, the library outputs a date string in the desired format. It provides following ways to date a HTML document:

1. Markup in header: common patterns are used to identify relevant elements (e.g. ``link`` and ``meta`` elements) including Open Graph protocol attributes and a large number of CMS idiosyncracies
1. HTML code: The whole document is then searched for structural markers: ``abbr/time`` elements and a series of attributes (e.g. *postmetadata*)
1. Bare HTML content: A series of heuristics is run on text and markup:

    - in fast mode the HTML page is cleaned and precise patterns are targeted
    - in extensive mode all potential dates are collected and disambiguation algorithm determines the best one

The module returns a date if a valid cue could be found in the document, corresponding to either the last update (default) or the original publishing statement. The output string defaults to ISO 8601 YMD format.

- Should be compatible with all common versions of Python 3
- Output thouroughly verified in terms of plausibility and adequateness
- Designed to be computationally efficient and used in production on millions of documents
- Batch processing of a list of URLs
- Switch between original and updated date



# State of the art

Diverse content extraction and scraping techniques are routinely used on web document collections by companies and research institutions alike. Content extraction mostly draws on Document Object Model (DOM) examination, that is on considering a given HTML document as a tree structure whose nodes represent parts of the document to be operated on.


## Alternatives

There are comparable solutions in Python, the following date extraction packages offer open-source and out-of-the-box:

- ``articleDateExtractor`` detects, extracts and normalizes the publication date of an online article or blog post [@articleDateExtractor],
- ``date_guesser`` extracts publication dates from a web pages along with an accuracy measure (not used here) [@dateguesser],
- ``goose3`` can extract information for embedded content [@goose3],
- ``htmldate`` is the software package described here, it is designed to extract original and updated publication dates of web pages [@Barbaresi:2019],
- ``newspaper`` is mostly geared towards newspaper texts [@newspaper],
- ``news-please`` is a news crawler that extracts structured information [@HamborgEtAl:2017],


## Benchmark

### Test set

The experiments below are run on a collection of documents which are either typical for Internet articles (news outlets, blogs, including smaller ones) or non-standard and thus harder to process. They were selected from large collections of web pages in German. For the sake of completeness a few documents in other languages were added (notably English, French, other European languages, Chinese and Arabic).

### Evaluation

Only documents with dates that are clearly to be determined are considered for this benchmark. A given day is taken as unit of reference, meaning that results are converted to ``%Y-%m-%d`` format if necessary in order to make them comparable. The evaluation script is available on the project repository: ``tests/comparison.py``. The tests can be reproduced by cloning the repository, installing all necessary packages and running the evaluation script with the data provided in the ``tests`` directory.

### Time

The execution time (best of 3 tests) cannot be easily compared in all cases as some solutions perform a whole series of operations which are irrelevant to this task. However, ``htmldate`` is noticeably faster than the strictly comparable packages (``articleDateExtractor`` and most certainly ``date_guesser``).

### Errors

``goose3``'s output isn't always meaningful and/or in a standardized format, these cases were discarded. news-please seems to have trouble with some encodings (e.g. in Chinese), in which case it leads to an exception.


## Results

The results below show that date extraction is not a completely solved task but one for which extractors have to resort to heuristics and guesses. The figures documenting recall and accuracy capture the real-world performance of the tools as the absence of a date output impacts the result.

| 200 web pages containing identifiable dates (2020-03-04)|
-----------------------------------------------------------
| Python Package 	| Precision 	| Recall 	| Accuracy 	| F-Score 	| Time |
------------------------------------------------------------------------------------------------
| newspaper 0.2.8 	| 0.917 	| 0.399 	| 0.385 	| 0.556 	| 78.6 |
| goose3 3.1.6 		| 0.910 	| 0.422 	| 0.405 	| 0.577 	| 13.5 |
| date_guesser 2.1.4 	| 0.825 	| 0.553 	| 0.495 	| 0.662 	| 36.7 |
| news-please 1.4.25 	| 0.831 	| 0.638 	| 0.565 	| 0.722 	| 64.5 |
| articleDateExtractor	| 0.20 		| 0.832 	| 0.644 	| 0.570 	| 0.726	| 5.7 |
| htmldate 0.6.1 (fast) | 0.917 	| 0.897 	| 0.830 	| 0.907 	| 2.2 |
| htmldate[all] 0.6.1 (extensive) | 0.899 	| 0.994 	| 0.895 	| 0.945 	| 5.4 |

Precision describes if the dates given as output are correct: ``newspaper`` and ``goose3`` fare well precision-wise but they fail to extract dates in a large majority of cases (poor recall). The difference in accuracy between ``date_guesser`` and ``newspaper`` is consistent with tests described on the website of the former.

It turns out that ``htmldate`` performs better than the other solutions overall. Most of all and despite being measured on a sample, the higher accuracy and faster processing time are highly significant. Especially for smaller news outlets, websites and blogs, as well as pages written in languages other than English (in this case mostly but not exclusively German), ``htmldate`` greatly extends date extraction coverage without sacrificing precision.


### Note on the different versions:

- ``htmldate[all]`` means that additional components are added for performance and coverage, which results in differences with respect to accuracy (due to further linguistic analysis) and potentially speed (faster date parsing). They can be installed with ``pip/pip3/pipenv htmldate[all]``.
- The fast mode does not output as many dates (lower recall) but its guesses are more often correct (better precision).


# Acknowledgements

This work has been supported by the ZDL research project (*Zentrum für digitale Lexikographie der deutschen Sprache*, (zdl.org)[https://www.zdl.org/]). Thanks to Yannick Kozmus and further (contributors)[https://github.com/adbar/htmldate/graphs/contributors] for working on and testing the package.

The following Python modules have been of help: ``lxml``, ``ciso8601``, and ``dateparser``. A few patterns are derived from ``python-goose``, ``metascraper``, ``newspaper`` and ``articleDateExtractor``. This module extends their coverage and robustness significantly.


# References



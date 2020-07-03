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
    affiliation: 1
affiliations:
 - name: Berlin-Brandenburg Academy of Sciences
   index: 1
date: 26 March 2020
bibliography: paper.bib
---



# Introduction


### Rationale


Metadata extraction is part of data mining and knowledge extraction techniques. Being able to better qualify content allows for insights based on descriptive or typological information (e.g. content type, authors or categories), better bandwidth control (e.g. by knowing when webpages have been updated), or optimization of indexing (e.g. caches or language-based heuristics). It is useful for applications including database management, business intelligence, or data visualization. This particular effort is part of a methodological approach to derive information from web documents in order to build text databases for research, chiefly linguistics and natural language processing. Dates are critical components since they are relevant both from a philological standpoint and in the context of information technology.

Although text is ubiquitous on the Web, extracting information from web pages can prove to be difficult. Web documents come in different shapes and sizes mostly because of the wide variety of genres, platforms or content management systems, and not least because of greatly diverse publication goals. In most cases, immediately accessible data on retrieved webpages do not carry substantial or accurate information: neither the URL nor the server response provide a reliable way to date a web document, that is to find out when it has been published or possibly modified. In that case it is necessary to fully parse the document or apply robust scraping patterns on it. Improving extraction methods for web collections can hopefully allow for combining both the quantity resulting from broad web crawling and the quality obtained by accurately extracting text and metadata and by rejecting documents which do not match certain criteria.


### Research context


Fellow colleagues are working on a lexicographic information platform [@GeykenEtAl:2017] at the language center of the Berlin-Brandenburg Academy of Sciences ([dwds.de](https://www.dwds.de/)). The platform hosts and provides access to a series of metadata-enhanced web corpora [@Barbaresi:2016]. Information on publication and modification dates is crucial to be able to make sense of linguistic data, that is in the case of lexicography to determine precisely when a given word has been used for the first time and how its use evolves through time.

Large "offline" web text collections are now standard among the research community in linguistics and natural language processing. The construction of such text corpora notably involves "crawling, downloading, 'cleaning' and de-duplicating the data, then linguistically annotating it and loading it into a corpus query tool." [@Kilgarriff:2007] Web crawling [@Olston:2010] involves a significant number of design decisions and turning points in data processing, without which data and applications turn into a "Wild West" [@JoGebru:2020]. Researchers face a lack of information regarding the content, whose adequacy, focus and quality are the object of a post hoc evaluation [@Baroni:2009]. Comparably, web corpora (i.e. document collections) usually lack metadata gathered with or obtained from documents. Between opportunistic and restrained data collection [@Barbaresi:2015], a significant challenge lies in the ability to extract and pre-process web data to meet scientific expectations with respect to corpus quality.


# Functionality


``htmldate`` finds original and updated publication dates of web pages using heuristics on HTML code and linguistic patterns. It operates both within Python and on the command-line. URLs, HTML files or HTML trees are given as input, and the library outputs a date string in the desired format or ``None`` as the output is thouroughly verified in terms of plausibility and adequateness.

The package features a combination of tree traversal and text-based extraction, the following methods are used to date HTML documents:

1. Markup in header: common patterns are used to identify relevant elements (e.g. ``link`` and ``meta`` elements) including Open Graph protocol attributes and a large number of content management systems idiosyncrasies
1. HTML code: The whole document is then searched for structural markers: ``abbr`` and ``time`` elements as well as a series of attributes (e.g. ``postmetadata``)
1. Bare HTML content: A series of heuristics is run on text and markup:

    - in ``fast`` mode the HTML page is cleaned and precise patterns are targeted
    - in ``extensive`` mode all potential dates are collected and a disambiguation algorithm determines the best one

Finally, a date is returned if a valid cue could be found in the document, corresponding to either the last update or the original publishing statement (the default), it allows for switching between original and updated dates. The output string defaults to ISO 8601 YMD format.

``htmldate`` is compatible with all recent versions of Python (currently 3.4 to 3.9). It is designed to be computationally efficient and used in production on millions of documents. All the steps needed from web page download to HTML parsing, scraping and text analysis are handled, including batch processing. It is distributed under the GNU General Public License v3.0.


# State of the art

Diverse extraction and scraping techniques are routinely used on web document collections by companies and research institutions alike. Content extraction mostly draws on Document Object Model (DOM) examination, that is on considering a given HTML document as a tree structure whose nodes represent parts of the document to be operated on. Less thorough and not necessarily faster alternatives use superficial search patterns such as regular expressions in order to capture desirable excerpts.


## Alternatives

There are comparable software solutions in Python, the following date extraction packages are open-source and work out-of-the-box:

- ``articleDateExtractor`` detects, extracts and normalizes the publication date of an online article or blog post [@articleDateExtractor],
- ``date_guesser`` extracts publication dates from a web pages along with an accuracy measure which is not tested here [@dateguesser],
- ``goose3`` can extract information for embedded content [@goose3],
- ``htmldate`` is the software package described here, it is designed to extract original and updated publication dates of web pages [@Barbaresi:2019],
- ``newspaper`` is mostly geared towards newspaper texts [@newspaper],
- ``news-please`` is a news crawler that extracts structured information [@HamborgEtAl:2017],


Two alternative packages are not tested here but could be used in addition:

- ``datefinder`` [@datefinder] features pattern-based date extraction for texts written in English,
- if dates are nowhere to be found using ``CarbonDate`` [@carbondate] can be an option, however this is computationally expensive.


## Benchmark

#### Test set

The experiments below are run on a collection of documents which are either typical for Internet articles (news outlets, blogs, including smaller ones) or non-standard and thus harder to process. They were selected from large collections of web pages in German. For the sake of completeness a few documents in other languages were added (English, European languages, Chinese and Arabic).

#### Evaluation

The evaluation script is available on the project repository: ``tests/comparison.py``. The tests can be reproduced by cloning the repository, installing all necessary packages and running the evaluation script with the data provided in the ``tests`` directory.

Only documents with dates that are clearly to be determined are considered for this benchmark. A given day is taken as unit of reference, meaning that results are converted to ``%Y-%m-%d`` format if necessary in order to make them comparable.

#### Time

The execution time (best of 3 tests) cannot be easily compared in all cases as some solutions perform a whole series of operations which are irrelevant to this task.

#### Errors

``goose3``'s output is not always meaningful and/or in a standardized format, these cases were discarded. news-please seems to have trouble with some encodings (e.g. in Chinese), in which case it leads to an exception.


## Results

The results in Table 1 show that date extraction is not a completely solved task but one for which extractors have to resort to heuristics and guesses. The figures documenting recall and accuracy capture the real-world performance of the tools as the absence of a date output impacts the result.


| Python Package | Precision | Recall | Accuracy | F-Score | Time |
| --- | --- | --- | --- | --- | --- |
| newspaper 0.2.8 	| 0.888 	| 0.407 	| 0.387 	| 0.558 	| 81.6 |
| goose3 3.1.6 		| 0.887 	| 0.441 	| 0.418 	| 0.589 	| 15.5 |
| date_guesser 2.1.4 	| 0.809 	| 0.553 	| 0.489 	| 0.657 	| 40.0 |
| news-please 1.5.3  	| 0.822 	| 0.655 	| 0.573 	| 0.729 	| 69.6 |
| articleDateExtractor 0.20 | 0.817 	| 0.635 	| 0.556 	| 0.714		| 7.0 |
| htmldate 0.6.3 *(fast)* | **0.903** 	| 0.907 	| 0.827 	| 0.905 	| **2.4** |
| htmldate[all] 0.6.3 *(extensive)* | 0.893 	| **1.000** 	| **0.893** 	| **0.944** 	| 5.7 |

: 225 web pages containing identifiable dates (as of 2020-06-17)


Precision describes if the dates given as output are correct: ``newspaper`` and ``goose3`` fare well precision-wise but they fail to extract dates in a large majority of cases (poor recall). The difference in accuracy between ``date_guesser`` and ``newspaper`` is consistent with tests described on the website of the former.

It turns out that ``htmldate`` performs better than the other solutions overall. It is also noticeably faster than the strictly comparable packages (``articleDateExtractor`` and ``date_guesser``). Despite being measured on a sample, the higher accuracy and faster processing time are highly significant. Especially for smaller news outlets, websites and blogs, as well as pages written in languages other than English (in this case mostly but not exclusively German), ``htmldate`` greatly extends date extraction coverage without sacrificing precision.



#### Note on the different versions:

- ``htmldate[all]`` means that additional components are added for performance and coverage. They can be installed with ``pip/pip3/pipenv htmldate[all]`` and result in differences with respect to accuracy (due to further linguistic analysis) and potentially speed (faster date parsing).
- The fast mode does not output as many dates (lower recall) but its guesses are more often correct (better precision).


# Acknowledgements

This work has been supported by the ZDL research project (*Zentrum für digitale Lexikographie der deutschen Sprache*, [zdl.org](https://www.zdl.org/)). Thanks to Yannick Kozmus and further [contributors](https://github.com/adbar/htmldate/graphs/contributors) for testing and working on the package.

The following Python modules have been of great help: ``lxml``, ``ciso8601``, and ``dateparser``. A few patterns are derived from ``python-goose``, ``metascraper``, ``newspaper`` and ``articleDateExtractor``; this package extends their coverage and robustness significantly.


# References



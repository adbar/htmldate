Evaluation
==========


Although text is ubiquitous on the Web, extracting information from web pages can prove to be difficult. In most cases, immediately accessible data on retrieved webpages do not carry substantial or accurate information: neither the URL nor the server response provide a reliable way to date a web document, that is find when it was written or modified. Content extraction mostly draws on Document Object Model (DOM) examination, that is on considering a given HTML document as a tree structure whose nodes represent parts of the document to be operated on. Less thorough and not necessarily faster alternatives use superficial search patterns such as regular expressions in order to capture desirable excerpts.


Alternatives
------------

There are comparable software solutions in Python, the following date extraction packages are open-source and work out-of-the-box:

- `articleDateExtractor <https://github.com/Webhose/article-date-extractor>`_ detects, extracts and normalizes the publication date of an online article or blog post,
- `date_guesser <https://github.com/mitmedialab/date_guesser>`_ extracts publication dates from a web pages along with an accuracy measure (not used here),
- `goose3 <https://github.com/goose3/goose3>`_ can extract information for embedded content,
- `htmldate <https://github.com/adbar/htmldate>`_ is the software package described here, it is designed to extract original and updated publication dates of web pages,
- `newspaper <https://github.com/codelucas/newspaper>`_ is mostly geared towards newspaper texts,
- `news-please <https://github.com/fhamborg/news-please>`_ is a news crawler that extracts structured information.

Two alternative packages are not tested here but could be used in addition:

- `datefinder <https://github.com/akoumjian/datefinder>`_ features pattern-based date extraction for texts written in English,
- if the date is nowhere to be found `carbon dating <https://github.com/oduwsdl/CarbonDate>`_ the web page can be an option, however this is computationally expensive.


Description
-----------

**Test set**: the experiments below are run on a collection of documents which are either typical for Internet articles (news outlets, blogs, including smaller ones) or non-standard and thus harder to process. They were selected from `large collections of web pages in German <https://www.dwds.de/d/k-web>`_. For the sake of completeness a few documents in other languages were added (mostly in English and French but also in other European languages, Chinese, Japanese and Arabic).

**Evaluation**: only documents with dates that are clearly to be determined are considered for this benchmark. A given day is taken as unit of reference, meaning that results are converted to ``%Y-%m-%d`` format if necessary in order to make them comparable. The evaluation script is available on the project repository: `tests/comparison.py <https://github.com/adbar/htmldate/blob/master/tests/comparison.py>`_. To reproduce the tests just clone the repository, install all necessary packages and run the evaluation script with the data provided in the *tests* directory.

**Time**: the execution time (best of 3 tests) cannot be easily compared in all cases as some solutions perform a whole series of operations which are irrelevant to this task.

**Errors:** *goose3*'s output isn't always meaningful and/or in a standardized format, these cases were discarded. *news-please* seems to have trouble with some encodings (e.g. in Chinese), in which case it leads to an exception.


Results
-------

The results below show that **date extraction is not a completely solved task** but one for which extractors have to resort to heuristics and guesses. The figures documenting recall and accuracy capture the real-world performance of the tools as the absence of a date output impacts the result.


=============================== ========= ========= ========= ========= =======
500 web pages containing identifiable dates (as of 2021-09-24)
-------------------------------------------------------------------------------
Python Package                  Precision Recall    Accuracy  F-Score   Time
=============================== ========= ========= ========= ========= =======
articleDateExtractor 0.20       0.769     0.691     0.572     0.728     3.3x
date_guesser 2.1.4              0.738     0.544     0.456     0.626     20x
goose3 3.1.9                    0.821     0.453     0.412     0.584     8.2x
htmldate[all] 0.9.1 (fast)      **0.839** 0.906     0.772     0.871     **1x**
htmldate[all] 0.9.1 (extensive) 0.825     **0.990** **0.818** **0.900** 1.7x
newspaper3k 0.2.8               0.729     0.630     0.510     0.675     8.4x
news-please 1.5.21              0.769     0.691     0.572     0.728     30x
=============================== ========= ========= ========= ========= =======


Additional data for new pages in English collected by the `Data Culture Group <https://dataculturegroup.org>`_ at Northeastern University.

Precision describes if the dates given as output are correct: *goose3* fares well precision-wise but it fails to extract dates in a large majority of cases (poor recall). The difference in accuracy between *date_guesser* and *newspaper* is consistent with tests described on the `website of the former <https://github.com/mitmedialab/date_guesser>`_.

It turns out that *htmldate* performs better than the other solutions overall. It is also noticeably faster than the strictly comparable packages (*articleDateExtractor* and most certainly *date_guesser*). Despite being measured on a sample, **the higher accuracy and faster processing time are highly significant**. Especially for smaller news outlets, websites and blogs, as well as pages written in languages other than English (in this case mostly but not exclusively German), *htmldate* greatly extends date extraction coverage without sacrificing precision.


Note on the different versions:

- *htmldate[all]* means that additional components are added for performance and coverage, which results in differences with respect to accuracy (due to further linguistic analysis) and potentially speed (faster date parsing). They can be installed with ``pip/pip3/pipenv htmldate[all]``.
- The fast mode does not output as many dates (lower recall) but its guesses are more often correct (better precision).


Older Results
-------------


=============================== ========= ========= ========= ========= =======
225 web pages containing identifiable dates (as of 2020-07-29)
-------------------------------------------------------------------------------
Python Package                  Precision Recall    Accuracy  F-Score   Time
=============================== ========= ========= ========= ========= =======
articleDateExtractor 0.20       0.817     0.635     0.556     0.714     6.8
date_guesser 2.1.4              0.809     0.553     0.489     0.657     40.0
goose3 3.1.6                    0.887     0.441     0.418     0.589     15.5
htmldate 0.7.0 (fast)           **0.903** 0.907     0.827     0.905     **2.4**
htmldate[all] 0.7.0 (extensive) 0.889     **1.000** **0.889** **0.941** 3.8
newspaper 0.2.8                 0.888     0.407     0.387     0.558     81.6
news-please 1.5.3               0.823     0.660     0.578     0.732     69.6
=============================== ========= ========= ========= ========= =======


=============================== ========= ========= ========= ========= =======
225 web pages containing identifiable dates (as of 2020-11-03)
-------------------------------------------------------------------------------
Python Package                  Precision Recall    Accuracy  F-Score   Time
=============================== ========= ========= ========= ========= =======
articleDateExtractor 0.20       0.817     0.635     0.556     0.714     3.5x
date_guesser 2.1.4              0.809     0.553     0.489     0.657     21x
goose3 3.1.6                    0.887     0.441     0.418     0.589     7.7x
htmldate[all] 0.7.2 (fast)      **0.899** 0.917     0.831     0.908     **1x**
htmldate[all] 0.7.2 (extensive) 0.893     **1.000** **0.893** **0.944** 1.6x
newspaper3k 0.2.8               0.888     0.407     0.387     0.558     40x
news-please 1.5.13              0.823     0.660     0.578     0.732     31x
=============================== ========= ========= ========= ========= =======

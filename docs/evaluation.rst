Evaluation
==========


Although text is ubiquitous on the Web, extracting information from web pages can be a difficult task. Easily accessible data often lacks substance or accuracy. Specifically, the URL and server response do not provide a reliable way to determine when a web document was written or last modified.

To overcome this challenge, content extraction typically involves the Document Object Model (DOM) of an HTML document. This approach treats the document as a tree structure, where each node represents a part of the document that can be operated on. While this method is thorough, there are alternative approaches using superficial search patterns, such as regular expressions, to capture specific text parts. However, these alternatives may not be as effective or efficient.

To run the evaluation, see `evaluation README <https://github.com/adbar/htmldate/blob/master/tests/README.rst>`_.


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

**Time**: the execution time cannot be easily compared in all cases as some solutions perform a whole series of operations which are irrelevant to this task.

**Errors:** *goose3*'s output isn't always meaningful and/or in a standardized format, these cases were discarded. *news-please* seems to have trouble with some encodings (e.g. in Chinese), in which case it leads to an exception.


Results
-------

The results below show that **date extraction is not a completely solved task** but one for which extractors have to resort to heuristics and guesses. The figures documenting recall and accuracy capture the real-world performance of the tools as the absence of a date output impacts the result.


=============================== ========= ========= ========= ========= =======
1000 web pages containing identifiable dates (as of 2023-11-13 on Python 3.10)
-------------------------------------------------------------------------------
Python Package                  Precision Recall    Accuracy  F-Score   Time
=============================== ========= ========= ========= ========= =======
articleDateExtractor 0.20       0.803     0.734     0.622     0.767     5x
date_guesser 2.1.4              0.781     0.600     0.514     0.679     18x
goose3 3.1.17                   0.869     0.532     0.493     0.660     15x
htmldate[all] 1.6.0 (fast)      **0.883** 0.924     0.823     0.903     **1x**
htmldate[all] 1.6.0 (extensive) 0.870     **0.993** **0.865** **0.928** 1.7x
newspaper3k 0.2.8               0.769     0.667     0.556     0.715     15x
news-please 1.5.35              0.801     0.768     0.645     0.784     34x
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
500 web pages containing identifiable dates (as of 2022-11-28 on Python 3.8)
-------------------------------------------------------------------------------
Python Package                  Precision Recall    Accuracy  F-Score   Time
=============================== ========= ========= ========= ========= =======
articleDateExtractor 0.20       0.769     0.691     0.572     0.728     4x
date_guesser 2.1.4              0.738     0.544     0.456     0.626     16x
goose3 3.1.12                   0.821     0.453     0.412     0.584     14x
htmldate[all] 1.4.0 (fast)      **0.856** 0.921     0.798     0.888     **1x**
htmldate[all] 1.4.0 (extensive) 0.847     **0.991** **0.840** **0.913** 2.2x
newspaper3k 0.2.8               0.729     0.630     0.510     0.675     13x
news-please 1.5.22              0.769     0.691     0.572     0.728     38x
=============================== ========= ========= ========= ========= =======



=============================== ========= ========= ========= ========= =======
500 web pages containing identifiable dates (as of 2022-03-23 on Python 3.8)
-------------------------------------------------------------------------------
Python Package                  Precision Recall    Accuracy  F-Score   Time
=============================== ========= ========= ========= ========= =======
articleDateExtractor 0.20       0.769     0.691     0.572     0.728     4.4x
date_guesser 2.1.4              0.738     0.544     0.456     0.626     17x
goose3 3.1.11                   0.821     0.453     0.412     0.584     15x
htmldate[all] 1.2.1 (fast)      **0.848** 0.921     0.790     0.883     **1x**
htmldate[all] 1.2.1 (extensive) 0.839     **0.990** **0.832** **0.908** 2.3x
newspaper3k 0.2.8               0.729     0.630     0.510     0.675     12x
news-please 1.5.21              0.769     0.691     0.572     0.728     40x
=============================== ========= ========= ========= ========= =======


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

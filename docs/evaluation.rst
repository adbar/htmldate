Evaluation
==========


Although text is ubiquitous on the Web, extracting information from web pages can prove to be difficult. The following evaluation features out-of-the-box solutions for Python.


Alternatives
------------

- `articleDateExtractor <https://github.com/Webhose/article-date-extractor>`_ detects, extracts and normalizes the publication date of an online article or blog post,
- `date_guesser <https://github.com/mitmedialab/date_guesser>`_ extracts publication dates from a web pages along with an accuracy measure (not used here),
- `goose3 <https://github.com/goose3/goose3>`_ can extract information for embedded content,
- `newspaper3k <https://github.com/codelucas/newspaper>`_ is mostly geared towards newspaper texts,
- `news-please <https://github.com/fhamborg/news-please>`_ is a news crawler that extracts structured information,

Last but not least, `htmldate <https://github.com/adbar/htmldate>`_ is the software package described here, it is designed to extract original and updated publication dates of web pages using common patterns, heuristics and robust extraction.


Description
-----------

**Test set**: the experiments below are run on a collection of documents which are either typical for Internet articles (news outlets, blogs, including smaller ones) or randomly selected from `large collections of web pages in German <https://www.dwds.de/d/k-web>`_. For the sake of completeness a few documents in other languages were added.

**Evaluation**: only documents with dates that are clearly to be determined are considered for this benchmark. A given day is taken as unit of reference, meaning that results are converted to ``%Y-%m-%d`` format if necessary in order to make them comparable. The evaluation script is available on the project repository: `tests/comparison.py <https://github.com/adbar/htmldate/blob/master/tests/comparison.py>`_. To reproduce the tests just clone the repository, install all necessary packages and run the evaluation script with the data provided in the *tests* directory.

**Time**: the execution time is not to be taken too seriously as some solutions performs a whole series of operations which are irrelevant to this task. *htmldate* seems to be faster than the strictly comparable packages (*articleDateExtractor* and most certainly *date_guesser*).

**Errors**: *goose3* sometimes outputs dates that are not meaningful and/or in a standardized format.


Results
-------

=============================== ========= ========  ========
100 documents containing identifiable dates (2020-02-12)
------------------------------------------------------------
Python Package                  Precision Accuracy  Time
=============================== ========= ========  ========
newspaper3k 0.2.8               **0.97**  0.31      49.51
goose3 3.1.6                    0.94      0.32      7.10
date_guesser 2.1.4              0.80      0.40      18.26
news-please 1.4.25              0.80      0.46      40.85
articleDateExtractor 0.20       0.81      0.46      2.13
htmldate 0.6.1 (fast)           0.93      0.79      1.40
htmldate[all] 0.6.1 (fast)      0.93      0.79      **1.35**
htmldate 0.6.1 (extensive)      0.88      0.88      1.44
htmldate[all] 0.6.1 (extensive) 0.91      **0.91**  2.67
=============================== ========= ========  ========

The accuracy captures the real-world performance of the tools, as the absence of a date impacts the result. The precision describes if the dates given as output are correct: *newspaper3k* and *goose3* have a small advantage but they fail to extract dates in the large majority of these cases.

The difference in accuracy between *date_guesser* and *newspaper3k* is consistent with tests described on the `website of the former <https://github.com/mitmedialab/date_guesser>`_.

It turns out that *htmldate* performs better than the other solutions overall. Most of all and despite being measured on a sample, the higher accuracy and faster processing time are highly significant. Especially for smaller news outlets, websites and blogs, as well as pages written in German (but not exclusively), *htmldate* greatly extends date extraction coverage without sacrificing precision.


**Note on the different versions:**

*htmldate[all]* means that additional components are added for performance and coverage. They can result in smaller differences with respect to accuracy (due to further linguistic analysis) and speed (faster date parsing). They can be installed with ``pip/pip3/pipenv htmldate[all]``.

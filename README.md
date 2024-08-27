# Htmldate: Find the Publication Date of Web Pages

[![Python package](https://img.shields.io/pypi/v/htmldate.svg)](https://pypi.python.org/pypi/htmldate)
[![Python versions](https://img.shields.io/pypi/pyversions/htmldate.svg)](https://pypi.python.org/pypi/htmldate)
[![Documentation Status](https://readthedocs.org/projects/htmldate/badge/?version=latest)](https://htmldate.readthedocs.org/en/latest/?badge=latest)
[![Code Coverage](https://img.shields.io/codecov/c/github/adbar/htmldate.svg)](https://codecov.io/gh/adbar/htmldate)
[![Downloads](https://img.shields.io/pypi/dm/htmldate?color=informational)](https://pepy.tech/project/htmldate)
[![JOSS article reference DOI: 10.21105/joss.02439](https://img.shields.io/badge/JOSS-10.21105%2Fjoss.02439-brightgreen)](https://doi.org/10.21105/joss.02439)

<br/>

<img src="https://raw.githubusercontent.com/adbar/htmldate/master/docs/htmldate-logo.png" alt="Logo as PNG image" width="60%"/>

<br/>

Find **original and updated publication dates** of any web page. **On
the command-line or with Python**, all the steps needed from web page
download to HTML parsing, scraping, and text analysis are included. The
package is used in production on millions of documents and integrated by
[multiple
libraries](https://github.com/adbar/htmldate/network/dependents).


## In a nutshell

<br/>

<img src="https://raw.githubusercontent.com/adbar/htmldate/master/docs/htmldate-demo.gif" alt="Demo as GIF image" width="80%"/>

<br/>

### With Python

``` python
>>> from htmldate import find_date
>>> find_date('http://blog.python.org/2016/12/python-360-is-now-available.html')
'2016-12-23'
```

### On the command-line

``` bash
$ htmldate -u http://blog.python.org/2016/12/python-360-is-now-available.html
'2016-12-23'
```

## Features

-   Flexible input: URLs, HTML files, or HTML trees can be used as input
    (including batch processing).
-   Customizable output: Any date format (defaults to [ISO 8601
    YMD](https://en.wikipedia.org/wiki/ISO_8601)).
-   Detection of both original and updated dates.
-   Multilingual.
-   Compatible with all recent versions of Python.

### How it works

Htmldate operates by sifting through HTML markup and if necessary text
elements. It features the following heuristics:

1.  **Markup in header**: Common patterns are used to identify relevant
    elements (e.g. `link` and `meta` elements) including [Open Graph
    protocol](http://ogp.me/) attributes.
2.  **HTML code**: The whole document is searched for structural markers
    like `abbr` or `time` elements and a series of attributes (e.g.
    `postmetadata`).
3.  **Bare HTML content**: Heuristics are run on text and markup:
    -   In `fast` mode the HTML page is cleaned and precise patterns are
        targeted.
    -   In `extensive` mode all potential dates are collected and a
        disambiguation algorithm determines the best one.

Finally, the output is validated and converted to the chosen format.

## Performance

1000 web pages containing identifiable dates (as of 2023-11-13 on Python 3.10)

| Python Package | Precision | Recall | Accuracy | F-Score | Time |
| -------------- | --------- | ------ | -------- | ------- | ---- |
| articleDateExtractor 0.20 | 0.803 | 0.734 | 0.622 | 0.767 | 5x |
| date_guesser 2.1.4 | 0.781 | 0.600 | 0.514 | 0.679 | 18x |
| goose3 3.1.17 | 0.869 | 0.532 | 0.493 | 0.660 | 15x |
| htmldate\[all\] 1.6.0 (fast) | **0.883** | 0.924 | 0.823 | 0.903 | **1x** |
| htmldate\[all\] 1.6.0 (extensive) | 0.870 | **0.993** | **0.865** | **0.928** | 1.7x |
| newspaper3k 0.2.8 | 0.769 | 0.667 | 0.556 | 0.715 | 15x |
| news-please 1.5.35 | 0.801 | 0.768 | 0.645 | 0.784 | 34x |

For the complete results and explanations see [evaluation
page](https://htmldate.readthedocs.io/en/latest/evaluation.html).

## Installation

Htmldate is tested on Linux, macOS and Windows systems, it is compatible
with Python 3.8 upwards. It can notably be installed with `pip` (`pip3`
where applicable) from the PyPI package repository:

-   `pip install htmldate`
-   (optionally) `pip install htmldate[speed]`

The last version to support Python 3.6 and 3.7 is `htmldate==1.8.1`.

## Documentation

For more details on installation, Python & CLI usage, **please refer to
the documentation**:
[htmldate.readthedocs.io](https://htmldate.readthedocs.io/)

## License

This package is distributed under the [Apache 2.0
license](https://www.apache.org/licenses/LICENSE-2.0.html).

Versions prior to v1.8.0 are under GPLv3+ license.

## Author

This project is part of methods to derive information from web documents
in order to build [text databases for
research](https://www.dwds.de/d/k-web) (chiefly linguistic analysis and
natural language processing).

Extracting and pre-processing web texts to meet the exacting standards
is a significant challenge. It is often not possible to reliably
determine the date of publication or modification using either the URL
or the server response. For more information:

[![JOSS article reference DOI: 10.21105/joss.02439](https://img.shields.io/badge/JOSS-10.21105%2Fjoss.02439-brightgreen)](https://doi.org/10.21105/joss.02439)
[![Zenodo archive DOI: 10.5281/zenodo.3459599](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.3459599-blue)](https://doi.org/10.5281/zenodo.3459599)


``` shell
@article{barbaresi-2020-htmldate,
  title = {{htmldate: A Python package to extract publication dates from web pages}},
  author = "Barbaresi, Adrien",
  journal = "Journal of Open Source Software",
  volume = 5,
  number = 51,
  pages = 2439,
  url = {https://doi.org/10.21105/joss.02439},
  publisher = {The Open Journal},
  year = 2020,
}
```

-   Barbaresi, A. \"[htmldate: A Python package to extract publication
    dates from web pages](https://doi.org/10.21105/joss.02439)\",
    Journal of Open Source Software, 5(51), 2439, 2020. DOI:
    10.21105/joss.02439
-   Barbaresi, A. \"[Generic Web Content Extraction with Open-Source
    Software](https://hal.archives-ouvertes.fr/hal-02447264/document)\",
    Proceedings of KONVENS 2019, Kaleidoscope Abstracts, 2019.
-   Barbaresi, A. \"[Efficient construction of metadata-enhanced web
    corpora](https://hal.archives-ouvertes.fr/hal-01371704v2/document)\",
    Proceedings of the [10th Web as Corpus Workshop
    (WAC-X)](https://www.sigwac.org.uk/wiki/WAC-X), 2016.

You can contact me via my [contact page](https://adrien.barbaresi.eu/)
or [GitHub](https://github.com/adbar).

## Contributing

[Contributions](https://github.com/adbar/htmldate/blob/master/CONTRIBUTING.md)
are welcome as well as issues filed on the [dedicated
page](https://github.com/adbar/htmldate/issues).

Special thanks to the
[contributors](https://github.com/adbar/htmldate/graphs/contributors)
who have submitted features and bugfixes!

## Acknowledgements

Kudos to the following software libraries:

-   [lxml](http://lxml.de/),
    [dateparser](https://github.com/scrapinghub/dateparser)
-   A few patterns are derived from the
    [python-goose](https://github.com/grangier/python-goose),
    [metascraper](https://github.com/ianstormtaylor/metascraper),
    [newspaper](https://github.com/codelucas/newspaper) and
    [articleDateExtractor](https://github.com/Webhose/article-date-extractor)
    libraries. This module extends their coverage and robustness
    significantly.

# htmldate

## Description

Seamless extraction/scraping of dates in web pages. *htmldate* provides following ways to date documents, based on HTML parsing:

1. Starting from the header of the page, it uses common patterns to identify date fields.
1. If this is not successful, it then scans the whole document.
1. If no date cue could be found, it finally run a series of heuristics on the content.

Documentation and packaging should come soon.

Pull requests are welcome.


### Context

There are webpages for which neither the URL nor the server response provide a reliable way to date the document, i.e. find when it was written.

This module is part of methods to derive metadata from web documents in order to build text corpora for (computational) linguistic analysis. For more information:

* Barbaresi, Adrien. "[Efficient construction of metadata-enhanced web corpora](https://hal.archives-ouvertes.fr/hal-01348706/document)." 10th Web as Corpus Workshop. 2016.


## Usage

The module is programmed with python3 in mind. It takes the HTML document as input (string format) and returns a date when a valid cue could be found in the document. The output string defaults to [ISO 8601 YMD format](https://en.wikipedia.org/wiki/ISO_8601).

Direct installation over pip is possible (but not thoroughly tested): `pip3 install -e git+https://github.com/adbar/htmldate.git`


### Within Python

All the functions of the module are currently bundled in *htmldate*, the examples below use the external module [requests](http://docs.python-requests.org/).

In case the web page features clear metadata, the extraction is straightforward:
```python3
>>> import requests
>>> import htmldate

>>> r = requests.get('r = requests.get('https://www.theguardian.com/politics/2016/feb/17/merkel-eu-uk-germany-national-interest-cameron-justified')
')
>>> htmldate.find_date(r.text)
'2016-02-17'
```

A more advanced analysis is sometimes needed:
```python3
>>> r = requests.get('http://blog.python.org/2016/12/python-360-is-now-available.html')
>>> core.find_date(r.text)
# DEBUG analyzing: <h2 class="date-header"><span>Friday, December 23, 2016</span></h2>
# DEBUG result: 2016-12-23
'2016-12-23'
```

In the worst case, the module resorts to a wild guess:
```python3
>>> r = requests.get('https://github.com/scrapinghub/dateparser')
>>> htmldate.find_date(r.text)
'2017-07-01'
```

There are however pages for which no date can be found, ever:
```python3
>>> r = requests.get('https://example.com')
>>> htmldate.find_date(r.text)
>>>
```

### Command-line

A basic command-line interface is included:
```bash
$ wget -qO- "http://blog.python.org/2016/12/python-360-is-now-available.html" | htmldate
2016-12-23
```


## Additional information

### Kudos to...

* [lxml](http://lxml.de/)
* [dateparser](https://github.com/scrapinghub/dateparser) (although it's is still a bit slow)
* A few patterns are derived from [python-goose](https://github.com/grangier/python-goose/), [metascraper](https://github.com/ianstormtaylor/metascraper/) and [newspaper](https://github.com/codelucas/newspaper/).


### Contact

See my [contact page](http://adrien.barbaresi.eu/contact.html) for details.

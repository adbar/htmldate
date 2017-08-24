# htmldoc-dating

*htmldoc-dating* provides ways to date HTML documents. Starting from the header of the page, it uses common patterns to identify date fields. If this is not successful, it then scans the whole document. If no date cue could be found, it finally run a series of heuristics on the content.

Documentation and packaging should come soon.

There is still a lot to be done, pull requests are welcome!


### Context

There are webpages for which neither the URL nor the server response provide a reliable way to date the document, i.e. find when it was written.

This module is part of methods to derive metadata from web documents in order to build text corpora for (computational) linguistic analysis. For more information:

* Barbaresi, Adrien. "[Efficient construction of metadata-enhanced web corpora](https://hal.archives-ouvertes.fr/hal-01348706/document)." 10th Web as Corpus Workshop. 2016.


### Usage

The module is programmed with python3 in mind. It returns a date when a valid

```python3
>>> import requests
>>> import core

>>> r = requests.get('r = requests.get('https://www.theguardian.com/politics/2016/feb/17/merkel-eu-uk-germany-national-interest-cameron-justified')
')
>>> core.find_date(r.text)
'2016-02-17'

>>> r = requests.get('http://blog.python.org/2016/12/python-360-is-now-available.html')
>>> core.find_date(r.text)
# DEBUG analyzing: <h2 class="date-header"><span>Friday, December 23, 2016</span></h2>
# DEBUG result: 2016-12-23
'2016-12-23'
```

There are however pages for which no date can be found, ever:

```python3
>>> r = requests.get('https://example.com')
>>> core.find_date(r.text)
>>>
```


### Kudos to...

* [lxml](http://lxml.de/)
* [dateparser](https://github.com/scrapinghub/dateparser) (although it's is still a bit slow)
* A few patterns are derived from [python-goose](https://github.com/grangier/python-goose/), [metascraper](https://github.com/ianstormtaylor/metascraper/) and [newspaper](https://github.com/codelucas/newspaper/).


### Contact

See my [contact page](http://adrien.barbaresi.eu/contact.html) for details.

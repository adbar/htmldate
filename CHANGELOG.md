## Changelog


### 1.2.0
- better performance
- remove unnecessary ciso8601 dependency
- temporary fix for scrapinghub/dateparser#1045 bug

### 1.1.1
- bugfix: input encoding
- improved extraction coverage (#47)

### 1.1.0
- better handling of file encodings
- slight increase in accuracy, more efficient code

### 1.0.1
- maintenance release, code base cleaned
- command-line interface: `--version` added
- file parsing reviewed

### 1.0.0
- faster and more accurate encoding detection
- simplified code base
- include support for Python 3.10 and dropped support for Python 3.5

### 0.9.1
- improved generic date parsing (thanks @RadhiFadlillah)
- specific support for French and Indonesian (thanks @RadhiFadlillah)
- additional evaluation for English news sites (kudos to @coreydockser & @rahulbot)
- bugs fixed

### 0.9.0
- improved exhaustive search
- simplified code
- bug fixes
- removed support for Python 3.4

### 0.8.1
- bugfixes

### 0.8.0
- `dateparser` and `regex` modules fully integrated
- patterns added for coverage
- smarter HTML doc loading

### 0.7.3
- dependencies updated and reduced: switch from `requests` to bare `urllib3`, make `chardet` standard and `cchardet` optional
- fixes: downloads, `OverflowError` in extraction

### 0.7.2
- compatibility with Python 3.9
- better speed and accuracy

### 0.7.1
- technical release: package requirements and docs wording

### 0.7.0
- code base and performance improved
- minimum date available as option
- support for Turkish patterns and CMS idiosyncrasies (thanks @evolutionoftheuniverse)

### 0.6.3
- more efficient code
- additional evaluation data

### 0.6.2
- performance and documentation improved

### 0.6.1
- code base restructured
- bugs fixed and further tests
- restored retro-compatibility with Python 3.4

### 0.6.0
- reduced number of packages dependencies
- introduced and tested optional dependencies
- more detailed documentation on readthedocs

### 0.5.6
- tests on Windows
- compataibility and code linting

### 0.5.5
- tests on Linux & MacOS
- bugs removed

### 0.5.4
- manually set maximum date
- better precision
- temporarily dropped support for Python 3.4

### 0.5.3
- coverage extension

### 0.5.2
- small bugs and coverage issues removed
- streamlined utils
- documentation added

### 0.5.1
- bugs corrected and cleaner code
- more errors caught and better test coverage

### 0.5.0
- significant speed-up after code profiling
- better support of free text detection (DE/EN)

### 0.4.1
- fixed lxml dependency
- reordered XPath-expressions

### 0.4.0
- refined and combined XPath-expressions
- better extraction of dates in free text
- better coverage and consistency issues solved

### 0.3.1
- improved consistency and further tests

### 0.3.0
- improvements in markup analysis along with more tests
- higher resolution for free text detection (e.g. DD/MM/YY)
- download mode (serial on command-line)

### 0.2.2
- better code consistency
- tested for Python2 and 3 with tox and coverage stats

### 0.2.1
- refined date comparisons
- debug and logging options
- more tests and test files
- extensive search can be disabled

### 0.2.0
- refined targeting of HTML structure
- better extraction logic for plain text cases
- further tests

### 0.1.2
- better extraction
- logging
- further tests
- settings

### 0.1.1
- tests functions (tox and pytest)
- retro-compatibility (python2)
- minor improvements

### 0.1.0
- minimum viable package

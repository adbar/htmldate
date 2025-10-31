## Changelog

## 1.9.4
- maintenance: remove LXML version constraint (#184)

## 1.9.3
- extraction: add heuristics (#173)
- maintenance: explicitly support Python 3.13 (#172)
- tests: better coverage (#175)
- docs: update images and contributing (#180)

## 1.9.2
- maintenance: explicit re-export and code quality (#168)
- setup: remove pytest.ini (#167)
- update dependencies

## 1.9.1
- fix: more robust copyright parsing (#165)
- cleaning fix: safer element removal (2735620)

## 1.9.0
- focus on Python 3.8+, use pyproject.toml file and update setup (#150, #153, #160)
- revamp tests and evaluation (#151)
- simplify code parts (#152)
- docs: convert readme to markdown (#147)

## 1.8.1
- fix: more restrictive YYYYMM pattern to prevent ValueError with @b3n4kh (#145)
- maintenance: add pre-commit with checks with @nadasuhailAyesh12 (#142)

## 1.8.0
- change license to Apache 2.0 (#140)
- compile XPath expressions (#136)
- update docs with @EkaterineSheshelidze (#135)

## 1.7.0
- fix meta property updated vs. original behavior (#121)
- support for LXML version 5.0+ (#127)
- fix image links in Readme

## 1.6.1
- fix for MacOS: pin LXML dependency with @adamh-oai

## 1.6.0
- focus on precision, stricter extraction patterns (#103, #105, #106, #112)
- simplified code base (#108, #109)
- replaced lxml.html.Cleaner (#104)
- extended evaluation

## 1.5.2
- fix for missing months keys in custom extractor (#100)
- fix for None in `try_date_expr()` (#101)

## 1.5.1
- fix regression for fast extraction introduced in e8b3538 (#96)
- fix setup by making backports-datetime-fromisoformat optional (#95)

## 1.5.0
- slightly higher accuracy with revised heuristics
- simplified code structure for better performance
- setup: support for 3.12, fromisoformat backport if applicable
- HTML parsing fixes: more lenient parsing, pinned LXML version for MacOS

## 1.4.3
- maintenance release: upgrade `urllib3` dependency

## 1.4.2
- support min_date/max_date as datetimes or datetime strings with @kernc (#73)
- add date attributes to HTML extraction with @kernc (#74)
- fix for extraction of updated and original dates in time elements
- code refactoring and maintenance

## 1.4.1
- better coverage of relevant HTML attributes
- automatically define upper time bound at each function call (#70)
- reviewed and simplified extraction code
- cache validation for format diverging from `%Y-%m-%d`
- updated dependencies and removed real-world tests from package

## 1.4.0
- additional search of free text in whole document (#67)
- optional parameter for subdaily precision with @getorca (#66)
- fix for HTML doctype parsing (#44)
- cleaner code for multilingual month expressions
- extended expressions for extraction in HTML meta fields
- update of dependencies and evaluation

## 1.3.2
- technical release: explicit support for Python 3.11 and logo

## 1.3.1
- fix for use of `min_date` & `max_date` (#62)
- simplified code & updated setup

### 1.3.0
- entirely type-checked code base
- new function `clear_caches()` (#57)
- slightly more efficient code (about 5% faster)

### 1.2.3
- fix for memory leak (#56)
- docs updated

### 1.2.2
- slightly higher accuracy & faster extensive extraction
- maintenance: code base simplified, more tests
- bugs addressed: #51, #54
- docs: fix by @MSK1582

### 1.2.1
- speed and accuracy gains
- better extraction coverage, simpler code
- bug fixed (typo in variable)

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

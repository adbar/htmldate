"""
Seamlessly extract the date of web pages based on header or body.
http://github.com/adbar/htmldate
"""

import re
from pathlib import Path
from setuptools import setup


# some problems with installation solved this way
extras = {
    'speed': [
        'cchardet >= 2.1.7', # ; python_version > "3.4"
        'ciso8601 >= 2.2.0',
        ],
}
extras['all'] = extras['speed']


def get_long_description():
    "Return the README"
    with open('README.rst', 'r', encoding='utf-8') as filehandle:
        long_description = filehandle.read()
    #long_description += "\n\n"
    #with open("CHANGELOG.md", encoding="utf8") as f:
    #    long_description += f.read()
    return long_description


def get_version(package):
    "Return package version as listed in `__version__` in `init.py`"
    # version = Path(package, '__init__.py').read_text() # Python >= 3.5
    with open(str(Path(package, '__init__.py')), 'r', encoding='utf-8') as filehandle:
        initfile = filehandle.read()
    return re.search('__version__ = [\'"]([^\'"]+)[\'"]', initfile).group(1)


setup(
    name='htmldate',
    version=get_version('htmldate'),
    description='Fast and robust extraction of original and updated publication dates from web pages.',
    long_description=get_long_description(),
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        #'Development Status :: 6 - Mature',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Text Processing :: Markup :: HTML',
    ],
    keywords=['datetime', 'date-parser', 'entity-extraction', 'html-extraction', 'html-parsing', 'metadata-extraction',  'webarchives', 'web-scraping'],
    url='http://github.com/adbar/htmldate',
    project_urls={
        "Source": "https://github.com/adbar/htmldate",
        "Coverage": "https://codecov.io/github/adbar/htmldate",
        "Tracker": "https://github.com/adbar/htmldate/issues",
    },
    author='Adrien Barbaresi',
    author_email='barbaresi@bbaw.de',
    license='GPLv3+',
    packages=['htmldate'],
    include_package_data=True,
    python_requires='>=3.5',
    install_requires=[
        'chardet == 3.0.4; python_version < "3.6"',
        'chardet >= 4.0.0; python_version >= "3.6"',
        'dateparser >= 1.0.0',
        'lxml >= 4.6.3',
        'python-dateutil >= 2.8.2',
        'regex >= 2021.8.28',
        'urllib3 >= 1.25, <2',
    ],
    extras_require=extras,
    entry_points = {
        'console_scripts': ['htmldate=htmldate.cli:main'],
    },
    # platforms='any',
    tests_require=['pytest'],
    zip_safe=False,
)

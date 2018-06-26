#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Seamlessly extract the date of web pages based on header or body.
http://github.com/adbar/htmldate
"""

from codecs import open # python2
import os
from setuptools import setup # find_packages,

#try:
#    from setuptools import setup
#except ImportError:
#    from distutils.core import setup



here = os.path.abspath(os.path.dirname(__file__))
packages = ['htmldate']


def readme():
    with open(os.path.join(here, 'README.rst'), 'r', 'utf-8') as readmefile:
        return readmefile.read()

setup(
    name='htmldate',
    version='0.3.3',
    description='This module can handle all the steps needed from web page download to HTML parsing, including scraping and textual analysis. Its goal is to find the creation date of a page all common structural patterns, text-based heuristics and robust date extraction. It takes URLs, HTML files or trees as input and outputs a date.',
    long_description=readme(),
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        #'Development Status :: 3 - Alpha',
        'Development Status :: 4 - Beta',
        #'Development Status :: 5 - Production/Stable',
        #'Development Status :: 6 - Mature',
        #'Development Status :: 7 - Inactive',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python',
        # 'Programming Language :: Python :: 2',
        #'Programming Language :: Python :: 2.6',
        # 'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        #'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Text Processing :: Markup :: HTML',
    ],
    keywords=['datetime', 'date-parser', 'entity-extraction', 'html-extraction', 'html-parsing', 'metadata-extraction',  'webarchives', 'web-scraping'],
    url='http://github.com/adbar/htmldate',
    author='Adrien Barbaresi',
    author_email='adrien.barbaresi@oeaw.ac.at',
    license='GPLv3+',
    packages=packages,
    include_package_data=True,
    install_requires=[
        'dateparser == 0.6.0',
        'lxml >= 4.0.0',
        'requests >= 2.18.0',
    ],
    # python_requires='>=3',
    entry_points = {
        'console_scripts': ['htmldate=htmldate.cli:main'],
    },
    # platforms='any',
    tests_require=['pytest', 'tox'],
    zip_safe=False,
)

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
    version='0.5.6',
    description='Find the creation date of web pages using a combination of tree traversal, common structural patterns, text-based heuristics and robust date extraction.',
    long_description=readme(),
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        #'Development Status :: 3 - Alpha',
        #'Development Status :: 4 - Beta',
        'Development Status :: 5 - Production/Stable',
        #'Development Status :: 6 - Mature',
        #'Development Status :: 7 - Inactive',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Text Processing :: Markup :: HTML',
    ],
    keywords=['datetime', 'date-parser', 'entity-extraction', 'html-extraction', 'html-parsing', 'metadata-extraction',  'webarchives', 'web-scraping'],
    url='http://github.com/adbar/htmldate',
    author='Adrien Barbaresi',
    author_email='barbaresi@bbaw.de',
    license='GPLv3+',
    packages=packages,
    include_package_data=True,
    install_requires=[
        'ciso8601 == 2.1.1',
        'dateparser == 0.7.2', # 0.5.0 is the fastest
        'lxml == 4.4.1', # CPython parser issue with version 4.3.1 # > 4.3.4 not compatible with Python 3.4
        'regex == 2019.08.19',
        'requests == 2.22.0',
    ],
    # python_requires='>=3',
    entry_points = {
        'console_scripts': ['htmldate=htmldate.cli:main'],
    },
    # platforms='any',
    tests_require=['pytest', 'tox'],
    zip_safe=False,
)
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
    version='0.1.2',
    description='Seamlessly extract the date of web pages based on the HTML code in order to determine the creation or modification date.',
    long_description=readme(),
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 2 - Pre-Alpha',
        #'Development Status :: 3 - Alpha',
        #'Development Status :: 4 - Beta',
        #'Development Status :: 5 - Production/Stable',
        #'Development Status :: 6 - Mature',
        #'Development Status :: 7 - Inactive',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Text Processing :: Markup :: HTML',
    ],
    keywords=['metadata-extraction', 'date-parser', 'html-parsing', 'webarchives'],
    url='http://github.com/adbar/htmldate',
    author='Adrien Barbaresi',
    author_email='adrien.barbaresi@oeaw.ac.at',
    license='GPLv3+',
    packages=packages,
    include_package_data=True,
    install_requires=[
        'dateparser >= 0.6.0',
        'lxml >= 3.7.0',
    ],
    # python_requires='>=3',
    entry_points = {
        'console_scripts': ['htmldate=htmldate.cli:main'],
    },
    # platforms='any',
    tests_require=['pytest', 'tox'],
    zip_safe=False,
)

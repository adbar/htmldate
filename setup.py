# -*- coding: utf-8 -*-
"""
Seamlessly extract the date of web pages based on header or body.
http://github.com/adbar/htmldate
"""

# from distutils.core import setup
import os
from setuptools import find_packages, setup

#try:
#    from setuptools import setup
#except ImportError:
#    from distutils.core import setup



def readme():
    here = os.path.abspath('.')
    with open(os.path.join(here, 'README.md'), encoding='utf-8') as readmefile:
        return readmefile.read()

setup(
    name='htmldate',
    version='0.1.0',
    description='Seamlessly extract/scrape the date of web pages based on a parse of the HTML code.',
    long_description=readme(),
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        #'Development Status :: 1 - Planning',
        'Development Status :: 2 - Pre-Alpha',
        #'Development Status :: 3 - Alpha',
        #'Development Status :: 4 - Beta',
        #'Development Status :: 5 - Production/Stable',
        #'Development Status :: 6 - Mature',
        #'Development Status :: 7 - Inactive',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        # 'Programming Language :: Python',
        # 'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering',
        'Topic :: Text Processing :: Linguistic',

    ],
    keywords=['metadata-extraction', 'date-parser', 'html-parsing', 'webarchives'],
    url='http://github.com/adbar/htmldate',
    author='Adrien Barbaresi',
    author_email='adrien.barbaresi@oeaw.ac.at',
    license='GPLv3+',
    packages=find_packages(exclude=['tests']), #['htmldate'],
    install_requires=[
        'dateparser >= 0.6.0',
        'lxml >= 3.7.0',
    ],
    entry_points = {
        'console_scripts': ['htmldate=htmldate.cli:main'],
    },
    platforms='any',
    #test_suite='nose.collector',
    #tests_require=['dateparser', 'lxml'],
    include_package_data=True,
    zip_safe=False,
)

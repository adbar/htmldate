"""
Seamlessly extract the date of web pages based on header or body.
http://github.com/adbar/htmldate
"""

# workaround for open() with encoding=''
from codecs import open

from os import path
from setuptools import setup


here = path.abspath(path.dirname(__file__))
packages = ['htmldate']


# some problems with installation solved this way
extras = {
    'all': [
        'ciso8601 >= 2.1.3',
        'dateparser >= 0.7.4',  # 0.5.0 could be faster
        'regex >= 2020.5.14',
        ],
}


def readme():
    with open(path.join(here, 'README.rst'), 'r', 'utf-8') as readmefile:
        return readmefile.read()

setup(
    name='htmldate',
    version='0.6.3',
    description='Fast and robust extraction of original and updated publication dates from web pages.',
    long_description=readme(),
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
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Internet :: WWW/HTTP',
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
    python_requires='>=3.4',
    install_requires=[
        'lxml == 4.3.5; python_version == "3.4"',
        'lxml >= 4.5.1; python_version > "3.4"',
        'python-dateutil >= 2.8.1',
        'requests == 2.21.0; python_version == "3.4"',
        'requests >= 2.23.0; python_version > "3.4"',
    ],
    extras_require=extras,
    entry_points = {
        'console_scripts': ['htmldate=htmldate.cli:main'],
    },
    # platforms='any',
    tests_require=['pytest'],
    zip_safe=False,
)

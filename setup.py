"""
Seamlessly extract the date of web pages based on URL, header or body.
http://github.com/adbar/htmldate
"""

import sys

from setuptools import setup


# add argument to compile with mypyc
if len(sys.argv) > 1 and sys.argv[1] == "--use-mypyc":
    sys.argv.pop(1)
    USE_MYPYC = True
    from mypyc.build import mypycify

    ext_modules = mypycify(
        [
            "htmldate/__init__.py",
            "htmldate/core.py",
            "htmldate/extractors.py",
            "htmldate/meta.py",
            "htmldate/settings.py",
            "htmldate/utils.py",
            "htmldate/validators.py",
        ],
        opt_level="3",
        multi_file=True,
    )
else:
    ext_modules = []


setup(
    # mypyc or not
    ext_modules=ext_modules,
)

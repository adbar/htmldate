Evaluation
==========

This evaluation focuses on the challenge of determining the publication date of a web document. Easily accessible data often lacks substance or accuracy. Specifically, the URL and server response do not provide a reliable way to determine when a web document was written or last modified.


Sources
-------

Principles
^^^^^^^^^^

The benchmark is run on a collection of documents which are either typical for Internet articles (news outlets, blogs, including smaller ones) or non-standard and thus harder to process. For the sake of completeness documents in multiple languages have been added.

Only documents with dates that are clearly to be determined are considered for this benchmark. A single day is taken as unit of reference (YMD format).

For more information see the `evaluation documentation page <https://htmldate.readthedocs.io/en/latest/evaluation.html>`_.


Date-annotated HTML pages
^^^^^^^^^^^^^^^^^^^^^^^^^

- BBAW collection (multilingual with a focus on German): Adrien Barbaresi, Shiyang Chen, Lukas Kozmus.
- Additional news pages (worldwide): `Data Culture Group <https://dataculturegroup.org>`_ at Northeastern University.


Reproducing the evaluation
--------------------------

1. Install the packages specified in ``eval-requirements.txt``
2. Run the script ``comparison.py`` (``--help`` for more options)


Hints:

- As different packages are installed it is recommended to create a virtual environment, for example with ``pyenv`` or ``venv``.
- Some packages are slow, to evaluate ``htmldate`` only run ``python3 comparison.py --small``.

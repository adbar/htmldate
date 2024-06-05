Evaluation
==========

Sources
-------

Date-annotated HTML pages
^^^^^^^^^^^^^^^^^^^^^^^^^

- BBAW collection (multilingual with a focus on German): Adrien Barbaresi, Shiyang Chen, Lukas Kozmus.
- Additional news pages (worldwide): `Data Culture Group <https://dataculturegroup.org>`_ at Northeastern University.


Reproducing the evaluation
--------------------------

Note: As different packages are installed it is recommended to create a virtual environment, for example with with ``pyenv`` or ``venv``.

1. Install the packages specified in ``eval-requirements.txt``
2. Run the script ``comparison.py``

Hint: Some packages are slow, to evaluate ``htmldate`` only run ``python3 comparison.py --small``.

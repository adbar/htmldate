# Sphinx configuration: https://www.sphinx-doc.org/en/master/usage/configuration.html

import os

import htmldate

project = 'htmldate'
copyright = '2017-2026, <a href="https://adrien.barbaresi.eu/">Adrien Barbaresi</a>'
author = 'Adrien Barbaresi'
version = release = htmldate.__version__

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx', 'sphinx.ext.viewcode']
autodoc_typehints = 'description'
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'lxml': ('https://lxml.de/apidoc/', None),
}
exclude_patterns = ['_build']

html_theme = 'shibuya'
html_logo = 'htmldate-logo.png'
html_static_path = ['_static']
html_css_files = ['accent.css']
html_baseurl = os.environ.get(
    'READTHEDOCS_CANONICAL_URL', 'https://htmldate.readthedocs.io/en/latest/'
)
html_theme_options = {
    'accent_color': 'amber',
    'github_url': 'https://github.com/adbar/htmldate',
    'og_image_url': 'https://raw.githubusercontent.com/adbar/htmldate/master/docs/htmldate-social.jpg',
    'show_ai_links': False,
}

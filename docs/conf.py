# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'chess_scanparsers'
copyright = '2024 CHESSComputing'
author = 'K. Soloway, R. Verberg'
release = 'PACKAGE_VERSION'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'myst_parser',
    'autodoc2',
    'sphinxarg.ext'
]
autodoc2_packages = [
    '../chess_scanparsers'
]
autodoc2_render_plugin = 'myst'
myst_enable_extensions = ['fieldlist']

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_static_path = ['_static']
html_show_copyright = False
html_theme = 'classic'
html_sidebars = {
    '**': ['globaltoc.html',
           'localtoc.html',
           'relations.html',
           'searchbox.html']
}

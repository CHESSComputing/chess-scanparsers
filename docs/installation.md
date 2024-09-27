# Installation

## Using `pip`
`chess-scanparser` is available over PyPI. Run
```bash
pip install chess-scanparsers
```
to install.

## From source
1. Clone the source repository from github.
   ```bash
   git clone https://github.com/CHESSComputing/chess-scanparser.git
   cd chess-scanparser
   ```
1. Set a valid version number. In `setup.py`, replace:
   ```{literalinclude} /../setup.py
   :language: python
   :start-after: '[set version]'
   :end-before: '[version set]'
   ```
   with
   ```python
   version = 'PACKAGE_VERSION'
   ```
1. Setup a local installation prefix for your version of python
   ```bash
   mkdir -p install/lib/python<yourpythonversion>/site-packages
   export PYTHONPATH=$PWD/install/lib/python<yourpythonversion>/site-packages
   ```
1. Use the setup script to install the package
   ```bash
   python setup.py install --prefix=$PWD/install
   ```

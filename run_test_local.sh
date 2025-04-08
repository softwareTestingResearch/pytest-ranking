#!/bin/bash

pip install .
pytest -xv

pip uninstall pytest-ranking

# # Push to PyPI
# rm -rf dist
# python3 -m build
# python3 -m twine upload dist/

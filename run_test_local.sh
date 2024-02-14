#!/bin/bash

pip install .
pytest -xv

pip uninstall pytest-tcp

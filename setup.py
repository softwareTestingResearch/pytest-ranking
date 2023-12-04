#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import codecs
from setuptools import setup


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding='utf-8').read()


setup(
    name='pytest-tcp',
    version='1.0.0',
    author='Max',
    author_email='testingresearch4all@gmail.com',
    maintainer='Max',
    maintainer_email='testingresearch4all@gmail.com',
    license='MIT',
    url='https://github.com/softwareTestingResearch/pytest-tcp',
    description='A Pytest plugin for test prioritization',
    long_description=read('README.rst'),
    py_modules=['pytest_tcp'],
    python_requires='>=3.5',
    install_requires=[
        'pytest>=7.4.3',
        'numpy'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Pytest',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
    entry_points={
        'pytest11': [
            'tcp = pytest_tcp',
        ],
    },
)

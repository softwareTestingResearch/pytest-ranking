#!/usr/bin/env python

import codecs
import os
from glob import glob
from os.path import basename, splitext

from setuptools import find_packages, setup


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding='utf-8').read()


setup(
    name='pytest-ranking',
    version='0.2.0',
    author='softwareTestingResearch',
    author_email='testingresearch4all@gmail.com',
    maintainer='softwareTestingResearch',
    maintainer_email='testingresearch4all@gmail.com',
    license='MIT',
    url='https://github.com/softwareTestingResearch/pytest-ranking',
    description='A Pytest plugin for automatically'
        + ' prioritizing/ranking tests to speed up failure detection',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
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
    keywords=[
        'pytest',
        'py.test',
        'test prioritization',
        'test ordering',
        'test ranking'
    ],
    entry_points={
        'pytest11': [
            'pytest_ranking = pytest_ranking.plugin',
        ],
    },
)

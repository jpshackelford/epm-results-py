#!/usr/bin/env python
from __future__ import print_function
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import io
import codecs
import os
import sys

#import epmresults

here = os.path.abspath(os.path.dirname(__file__))

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.txt', 'CHANGES.txt')

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name='epmresults',
    version='0.0.1',
    url='http://github.com/jpshackelford/epm-results-py/',
    license='MIT',
    author='John-Mason Shackelford',
    tests_require=['pytest'],
    install_requires=['Adafruit-GPIO>=1.0.3',
                      'service>=0.4.1',
                      'redis>=2.10.6',
                      'PyYAML>=3.12',
                      'pytz>=2018.3',
                      'pyaml>=17.12.1'
                     ],
    cmdclass={'test': PyTest},
    author_email='jpshack@gmail.com',
    description='Elevated Plus Maze Sensor Tools for Raspberry Pi',
    long_description=long_description,
    packages=['epmresults'],
    include_package_data=True,
    platforms='any',
    scripts = ['scripts/epmsensorsd'],
    test_suite='tests',
    classifiers = [
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        ],
    extras_require={
        'testing': ['pytest','mock']
    }
)
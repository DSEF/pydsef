import os
from setuptools import setup

setup(
    name = "pydsef",
    version = "0.1.2",
    author = "Samuel Thomas",
    author_email = "sgt43@cornell.edu",
    description = ("A python library that provides convience functions for DSEF"),
    packages = ['pydsef'],
    url = 'https://github.com/DSEF',
    license='MIT',
    install_requires=['rpyc', 'scp', 'pyyaml'],
    python_requires='>=3',
)

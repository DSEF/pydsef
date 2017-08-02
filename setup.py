import os
from setuptools import setup

setup(
    name = "pydsef",
    version = "0.1.0",
    author = ["Samuel Thomas", "Yousif Aldolaijan"],
    author_email = ["sgt43@cornell.edu", "yad999@gmail.com"],
    description = ("A python library that provides convience functions for DSEF"),
    packages = ['pydsef'],
    url = 'https://github.com/DSEF',
    license='MIT',
    install_requires=['rpyc', 'scp', 'yaml'],
    python_requires='>=3',
}

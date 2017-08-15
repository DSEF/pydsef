import os
from setuptools import setup
from sphinx.setup_command import BuildDoc
build_cmd = {'build_docs': BuildDoc}

name = 'pydsef'
version = '0.2.0'
setup(
    name = name,
    version = version,
	cmdclass = build_cmd,
	command_options = {
		'build_docs': {
			'project': ('setup.py', name),
			'version': ('setup.py', version),
			'release': ('setup.py', version),
			'source-dir': ('setup.py', 'doc/source'),
			'build-dir': ('setup.py', 'doc/build'),
			'all_files': ('setup.py', 1)
		}
	},
    author = "Samuel Thomas",
    author_email = "sgt43@cornell.edu",
    description = ("A python library that provides convience functions for DSEF"),
    packages = ['pydsef'],
    url = 'https://github.com/DSEF',
    license='MIT',
    install_requires=['rpyc', 'scp', 'pyyaml'],
    python_requires='>=3',
)

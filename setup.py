#!/usr/bin/env python

import os
import sys

sys.path.insert(0, os.path.abspath('lib'))
try:
        from setuptools import setup, find_packages
except ImportError:
        print("You need setuptools.")
        sys.exit(1)

setup(
    name='playbook-docgen',
    description='Tool for generating ansible playbook documentation.',
    author='Hidetoshi Hirokawa',
    license='GPLv3',
    install_requires=['ansible >= 2', 'jinja2', 'ruamel.yaml', 'setuptools'],
    package_dir={'': 'libs'},
    packages=find_packages('libs'),
    package_data={
        '': ['templates/*.j2'],
    },
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
    data_files=[],
)

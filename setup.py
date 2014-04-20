#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='docker-watcher',
    version="0.1",
    description='Monitor for Docker containers, supervisor-like',
    long_description='''Monitor for Docker containers, supervisor-like.''',
    keywords='python docker supervisor',
    author='Marinho Brandao',
    author_email='marinho@gmail.com',
    url='http://github.com/marinho/docker-watcher/',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
    ],
    packages=["docker_watcher"],
    install_requires=[
        "pytz",
    ],
    entry_points={"console_scripts": [
        "docker-watcher = docker_watcher.main:run",
        ]},
)


#!/usr/bin/env python
from pip.req import parse_requirements
from setuptools import setup, find_packages

import sprintly 

install_reqs = parse_requirements('requirements.txt')
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='sprintly',
    version=sprintly.__version__,
    description='API wrapper for Sprint.ly',
    author=sprintly.__author__,
    url='https://github.com/catskul/python-sprintly',
    packages=find_packages(),
    download_url='http://pypi.python.org/pypi/sprintly/',
    keywords='sprintly api wrapper',
    zip_safe=True,
    install_requires=reqs,
    py_modules=['sprintly'],
    classifiers=[
        'Development Status :: 3 - Alpha'
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)


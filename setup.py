#!/usr/bin/env python
from pip.req import parse_requirements
from setuptools import setup, find_packages

import sprintly.pkg_info

install_reqs = parse_requirements('requirements.txt')
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='sprintly',
    version=sprintly.pkg_info.__version__,
    description='API wrapper for Sprint.ly',
    author=sprintly.pkg_info.__author__,
    url='https://github.com/catskul/python-sprintly',
    packages=find_packages(),
    keywords='sprintly api wrapper',
    zip_safe=True,
    install_requires=reqs,
    scripts=['scripts/sprintly-cli'],
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


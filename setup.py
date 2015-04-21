#!/usr/bin/env python
import pip.req
import pip.download

from setuptools import setup, find_packages

execfile('sprintly/pkg_info.py')

install_reqs = pip.req.parse_requirements('requirements.txt', session=pip.download.PipSession())
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='sprintly',
    version=__version__,
    description='API wrapper for Sprint.ly',
    author=__author__,
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


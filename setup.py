# -*- coding: utf8 -*-
from os.path import join, dirname
from setuptools import setup


def read(fname):
    with open(join(dirname(__file__), fname)) as f:
        return f.read()


config = {
    'name': "czmake",
    'version': "0.6",
    'author': "Walter Oggioni",
    'author_email': "oggioni.walter@gmail.com",
    'description': ("Comelz build utility module."),
    'long_description': read('README.rst'),
    'license': "MIT",
    'keywords': "cmake",
    'url': "https://github.com/comelz/czmake",
    'packages': ['czmake'],
    'include_package_data': True,
    'package_data': {
        '': ['*.cmake'],
    },
    'classifiers': [
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Version Control',
        'Topic :: Utilities'
    ],
    "entry_points": {
        'console_scripts': [
            'czmake=czmake.build:run',
            'czconfigure=czmake.configure:run',
        ],
    }
}
setup(**config)

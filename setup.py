#! /usr/bin/env python
from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages
import sys, os

version = '0.5'

setup(name='OEBakery',
      version=version,
      description="OE-Bakery - OpenEmbedded Bakery SDK Tool",
      long_description="""\
OE-Bakery - A tool for making working with BitBake and OpenEmbedded easier""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author="Esben Haabendal",
      author_email="eha@doredevelopment.dk",
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
#      entry_points="""
#      # -*- Entry points: -*-
#      """,
      url="http://dev.doredevelopment.dk/wiki/OpenEmbeddedBakery",
      entry_points = {
        'console_scripts': [
            'oe = oebakery.oe:main',
            ]
        }
      )

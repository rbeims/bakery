#! /usr/bin/env python

#import sys
#import os
#sys.path.append(os.path.join(os.path.dirname(
#            os.path.abspath(sys.argv[0])),
#            "/setuptools/setuptools-0.6c11-py2.6.egg"))
#from ez_setup import use_setuptools
#use_setuptools()

import oebakery
version = oebakery.__version__

import sys
if "--version" in sys.argv:
    print version
    sys.exit(0)

from setuptools import setup, find_packages

try:
    import stdeb
except ImportError:
    print 'Warning: cannot find stdeb module'

setup(name='oe-lite',
      version=version,
      description="OE-lite - embedded Linux platform development kit",
      long_description="""\
A tool for building complete embedded Linux platforms""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author="Esben Haabendal",
      author_email="esben.haabendal@prevas.dk",
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      #packages=['oebakery'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      url="http://oe-lite.org/",
      entry_points = {
        'console_scripts': [
            'oe = oebakery.oe:main',
            ]
        }
      )

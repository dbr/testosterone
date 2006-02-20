#!/usr/bin/env python
from distutils.core import setup

classifiers = [
    'Development Status :: 4 - Beta'
  , 'Environment :: Console'
  , 'Intended Audience :: Developers'
  , 'License :: Freeware'
  , 'Natural Language :: English'
  , 'Operating System :: Unix'
  , 'Programming Language :: Python'
  , 'Topic :: Software Development :: Testing'
                ]

setup( name = 'testosterone'
     , version = '0.4'
     , package_dir = {'':'site-packages'}
     , packages = [ 'testosterone'
                  , 'testosterone.cli'
                  , 'testosterone.interactive'
                  , 'testosterone.interactive.screens'
                  , 'testosterone.tests'
                  , 'testosterone.tests.interactive'
                   ]
     , description = 'testosterone is a manly testing interface for Python.'
     , author = 'Chad Whitacre'
     , author_email = 'chad@zetaweb.com'
     , url = 'http://www.zetadev.com/software/testosterone/'
     , classifiers = classifiers
      )

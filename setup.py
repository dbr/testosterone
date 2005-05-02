#!/usr/bin/env python
from distutils.core import setup

classifiers = [
    'Development Status :: 4 - Beta'
  # 'Development Status :: 5 - Production/Stable'
  , 'Environment :: Console'
  , 'Intended Audience :: Developers'
  , 'License :: Freeware'
  , 'Natural Language :: English'
  , 'Operating System :: OS Independent'
  , 'Programming Language :: Python'
  , 'Topic :: Software Development :: Testing'
                ]

setup( name = 'pytest'
     , version = '0.3'
     , py_modules = ['ASTutils','PyTest']
     , scripts = ['pytest']
     , description = 'Pytest is a testing interpreter for Python.'
     , author = 'Chad Whitacre'
     , author_email = 'chad [at] zetaweb [dot] com'
     , url = 'http://www.zetadev.com/software/'
     , classifiers = classifiers
      )

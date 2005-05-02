#!/usr/bin/env python
from distutils.core import setup
from os import linesep

import pytest as base

description = base.__doc__.split(linesep+linesep)[0]
description = description.strip(linesep)

setup( name = base.__name__
     , version = base.__version__
     , py_modules = ['ASTutils']
     , description = description
     , author = base.__author__
     , author_email = base.__author_email__
     , url = base.__url__
      )

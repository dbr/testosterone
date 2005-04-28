#!/usr/bin/env pytest
# this works ^^^^^^^^

"""

Pytest is a testing framework for Python. This tutorial will show you how to use
it. In general, testing is made up of three things:

    1. fixture -- the thing you want to test

    2. tests -- things you do to your fixture to see if it behaves as expected

    3. reports -- tests are worthless with their results are communicated to you

Other testing frameworks such as PyUnit (which is included in the standard
library as unittest) and Brah Cohen's testtest module


##
# The basics
##

# passing tests are silent; no output is reported
1 + 1 == 2

# a failing test produces output
1 + 1 == 3

# print statements also produce output
print 'hello world!'

# as do calls to pprint
from pprint import pprint
pprint('look ma! no burdensome framework!')

# in fact, all writes to stdout will be included in our report
sys.stdout.write('teehee!')




from pytest import utils


def foo():
    raise 'foo'
1 == foo()
def bar():
    return foo()
2 == bar()


##
# assertRaises functionality
##

class FooException(Exception):
    pass

def foo(bar, baz):
    raise FooException

exc = utils.catchException(foo, 1, baz=2)
exc is FooException


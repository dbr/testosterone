#!/usr/bin/env pytest

# Pytest is a testing interpreter for Python. This tutorial will show you how to
# use it.
#
# In general, testing is made up of three things:
#
#     1. fixture -- the thing you want to test the behavior of
#
#     2. tests -- things you do to your fixture to see if it behaves as expected
#
#     3. reports -- feedback on whether the fixture behaved as expected
#
# Pytest uses the Python language itself to define the first two of these. Which
# is to say, test scripts written for pytest are in fact just Python scripts.
# When run through pytest, however, all explicit comparison statements are
# interpreted as tests. Comparison statements are explicit if they have one or
# more comparison operators:
#
#       <           <=        in
#       >           <>        not in
#       ==          !=        is
#       >=                    is not
#
# For example:

1 + 1 == 2
1 in (1,2,3,4)
(5 in [1,2,3,4]) is not True

# Pytest interprets these as a test. However, since it evaluates to true -- i.e.,
# the test passes, you never hear about it specifically. Pytest only provides
# detailed reporting on failed tests, and tests which raise exceptions:

1 + 1 == 3 # failed test; will show up in output

def foo():
    raise 'bar'

foo() is True # the traceback will be printed in the report

# Aside from explicit comparisons, the only other thing pytest touches are print
# statements and calls to pprint. Output from print and pprint are funneled to
# the report


# print statements also produce output
print 'hello world!'
print 'hello world! hello world! hello world! hello world! hello world! hello world! hello world! '

# as do calls to pprint
from pprint import pprint
pprint('look ma! no burdensome framework!')

# in fact, all writes to stdout will be included in our report
#sys.stdout.write('teehee!')




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

#!/usr/bin/env pytest

##
# Introduction
##

# Pytest is a testing interpreter for Python. We call it an 'interpreter'
# rather than a 'framework' because tests written for pytest involve no
# framework per se other than the Python language itself. Pytests are regular
# old python scripts that are interpreted in a special way. This tutorial
# will explain and demonstrate how to use pytest.


##
# Section I: The Basics
##

# In general, testing is made up of three things:
#
#     1. fixture -- the thing you want to test the behavior of
#
#     2. tests -- things you do to your fixture to see if it behaves as expected
#
#     3. reports -- feedback on whether the fixture behaved as expected
#
#
# The idea behind pytest is that Python itself already gives us a very
# expressive language for defining fixture and tests. Any Python statement
# is basically building fixture:

foo = 'bar'

# And any Python conditional is basically a test:

foo == 'bar'

# So pytest uses the Python language as it stands to define fixture and tests.
# This is what it means that pytests are just Python scripts. However, when
# pytest interprets a Python script, it does some extra monitoring of the
# script's execution -- think of a scientist monitoring an experiment -- so that
# at the end it can output a report.

# More specifically, pytest treats all explicit, comparison statements as tests.
# Comparison statements are explicit if they have one or more comparison
# operators:
#
#       <           <=        in
#       >           <>        not in
#       ==          !=        is
#       >=                    is not
#
# For example:

1 + 1 == 2
1 + 1 + 1 + 1 == 2 + 2 == 4
mylist = [1,2,3,4]
1 in mylist
5 in mylist

# Pytest counts four tests in these five statements. The variable assignment is
# considered to be fixture and is executed unaltered by pytest. The tests,
# however, are monitored and their results are tallied. The first three tests
# evaluate to True and are therefore said to have 'passed.' The fourth test is
# 'failed' because it evaluates to False. Pytest will include detailed
# information on the failed test in its final report. The passing tests will be
# included in the report's summary but won't be mentioned explicitly.
#

# Once you've written a script that you'd like to run through pytest, you simply
# call it from the command line like so:
#
#   $ pytest myscript.pyt
#
# The 'pyt' extension indicates that this python script is intended for the
# pytest interpreter. It could be run through the standard python interpreter,
# but it probably wouldn't be very interesting, since test scripts generally
# don't do anything useful per se. See the "Usage Patterns" section below for
# more ideas here.

# So that's the basics: write a python script and run it through
#





def foo():
    raise 'bar'

foo() is True # the traceback will be printed in the report

# print statements also produce output
print 'hello world!'
print 'hello world! hello world! hello world! hello world! hello world! hello world! hello world! '

# as do calls to pprint
from pprint import pformat
print pformat('look ma! no burdensome framework!')

# in fact, all writes to stdout will be included in our report
#sys.stdout.write('teehee!')



# Aside from explicit comparisons, the only other thing pytest touches are print
# statements and calls to pprint. Output from print and pprint are funneled to
# the report






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



# printing
# looping
# exception handling
# usage patterns:
#   complements doctest -- similar philosophy
#   replaces unittest
#   tests in situ
#   separate testing script
#   working with the PyTest module directly
#   using non-standard python installations
# utils:
#   catching exceptions
#   reset button

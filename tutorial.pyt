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

# More specifically, pytest treats all explicit comparison statements as tests.
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
#   $ pytest tutorial.pyt
#
# The 'pyt' extension indicates that this python script is intended for the
# pytest interpreter. It could be run through the standard python interpreter,
# but it probably wouldn't be very interesting, since test scripts generally
# don't do anything useful per se. See the "Usage Patterns" section below for
# more ideas here.



##
# Section II: Further Detail
##

# Now that we understand the basics of pytest, let's round out the picture with
# some aspects of pytest that make it useful in the real world. We've seen a
# simple example of creating fixture in the variable assignment above:

mylist = [1,2,3,4]

# In fact, there are no limits on how we build fixture: we have the entire
# Python language at our disposal. For example, we could build a fixture using a
# 'for' loop:

mylist = [1,2,3,4,5,6,7,8,9,10]
foo = False
for i in mylist:
    if i == 8:
        foo = True

# And then we can test our fixture:

foo is False

# Going further, we could define and test a recursive function:

mylist = [1,2,3,[4,[5,6]],7,8,9,[10]]
def hasitem(seq, i):
    for x in seq:
        if type(x) is type([]):
            hasitem(x, i)
        elif x == i:
            return True
    return False # default

hasitem(mylist, 8) is True # test

# But why stop there? Here's a class with a recursive classmethod:

mylist = [1,2,3,8,[4,[5,6]],7,8,9,[10,8]]

class ilove8s:
    yummy8s = []
    def gimme8s(self, seq, i):
        for x in seq:
            if type(x) is type([]):
                self.gimme8s(x, i)
            elif x == i:
                self.yummy8s.append(x)
    gimme8s = classmethod(gimme8s)

ilove8s.gimme8s(mylist, 8)
len(ilove8s.yummy8s) == 3 # test

# Of course, what we *really* want to do is to build a fixture out of components
# that are defined elsewhere. No problem. Here's a little test for whether the
# random module lives up to its name:

from sets import Set
from random import choice

foo = Set()
for i in range(10):
    foo.add(choice(range(10)))

len(foo) > 1 # test


# further detail:
#   importing, classes, defs, loops
#   printing
#       whitespace
#   exception handling
#       SyntaxError within parsed code e.g.: 'mylist ='
#       SyntaxError caught earlier(?), e.g., comment w/o comment token
#       AST error: malformed code (indent level))
#       multiple small statements -> exception test (1 == 2; 3 == 1 + 2)

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



# utils:
#   catching exceptions
#   reset button
# usage patterns:
#   complements doctest -- similar philosophy
#   replaces unittest
#   tests in situ
#   separate testing script
#   working with the PyTest module directly
#   using non-standard python installations

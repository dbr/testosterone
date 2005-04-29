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
# Section II: Real World Examples
##

# Now that we understand the basics of pytest, let's round out the picture with
# some examples that are closer to the real world. We've seen a simple example
# of creating fixture in the variable assignment above:

mylist = [1,2,3,4]


# In fact, there are no limits on how we build fixture: we have the entire
# Python language at our disposal. For example, we could build a fixture using a
# 'for' loop:

mylist = []
for i in range(10):
    mylist.append(i)


# And then we can test our fixture:

8 in mylist


# Going further, there's no reason we couldn't define and test a recursive
# function (notice the use of 'is True' to explicitly test the function call):

mylist = [1,2,3,[4,[5,6]],7,8,9,[10]]

def has8(seq):
    for x in seq:
        if type(x) is type([]):
            has8(x)
        elif x == 8:
            return True
    return False # default

has8(mylist) is True # test


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



##
# Section III: The Report
##

# After it executes your test script, pytest will give you a report with the
# following summary information (printed at the top and bottom of the report):
#
#   - Name of the file being tested
#   - Number of passing tests
#   - Number of failed tests
#   - Number of tests that raised exceptions
#   - Total number of tests
#   - Total time it took to run the tests, in seconds
#
# Pytest will also give you a detailed report for the following:
#
#   - Failed tests
#   - Tests that raised exceptions
#
# This detail report includes what the statement was, what line number it was
# on, the value of all relevant terms (for failures), and a traceback (for
# exceptions).
#
# Additionally, you can explicitly insert information into the report using the
# print statement:

print 'hello world'
print >> sys.stdout, "this works too"


# Any calls to 'print' in your test script will appear in sequence in the final
# report, along with the original statement and the line number. However, there
# are several gotchas with this feature:
#
#   - Currently pprint.pprint does not behave similarly. The workaround is to
#     use pformat:

from pprint import pformat
print pformat(mylist)


#   - Neither does sys.stdout.write; we may leave this one alone altogether to
#     allow for manual manipulation of the report:

from os import linesep
sys.stdout.write('Anything written to stdout will appear in your report' +\
                 (linesep*3))

#   - Multi-line strings don't work. This is a bug. The workaround is to assign
#     to a variable, and then print the variable:

# print """\
# this will break pytest
# """

foo = '''\
    but this won't
'''
print foo


# As a final note, you will notice in the report that when statements are
# reproduced in the output, the whitespace may not exactly match the whitespace
# in the original file (comments will be lost as well). This is due to the way
# that pytest manipulates the source code and in no way affects the execution of
# the code.



##
# Section IV: Exception Handling
##

# Exception handling in pytest is somewhat complex, due to the different
# execution contexts employed. All tests and print statements are executed in a
# "laboratory" context. Any exceptions they raise will be caught, tallied, and
# included in the final report. Execution of the script as a whole will then
# be allowed to proceed unhindered. Here's an example:

def foo():
    raise RuntimeError, 'ouch!'

foo() is True # look for the traceback in the report


# Exceptions raised during print statements are also captured by pytest and
# included in the report, and execution proceeds:

print foo()


# Exceptions raised by fixture, however, are either caught very early or very
# late. In either case, they terminate execution of the script. If caught early,
# as in the case of SyntaxErrors, execution will terminate with no report being
# generated, and the standard traceback will be displayed:

# mylist =


# If caught late, then the script must be rerun as if it were a standard Python
# script (i.e., without pytest's monitoring interferences) in order for a useful
# traceback to be gathered. Pytest does this for you, but when it does, any
# prior test or print exceptions are also re-triggered, so that execution
# actually terminates with the first exception of any kind:

foo()


# The net effect of a late fixture exception, however, is that all exceptions up
# to and including the terminal exception are included in the final report. The
# last exception is labeled "CRISIS."
#
# Because tests are executed in a controlled environment, the tracebacks they
# produce may look a little goofy. As pytest gets more use I anticipate that this
# rough edge will be buffed a bit.
#
# If you need to test for a certain exception (the equivalent of PyUnit's
# assertRaises, you can use this idiom:

try:
    foo()
except:
    exc = sys.exc_info()[0]

exc is Exception


# The PyTest module on which pytest is based provides a utility class that has a
# convenience method for this:

def foo(bar, baz):
    raise Exception

from PyTest import utils
exc = catch_exc(foo, 1, baz='bar')
exc is Exception


# This is currently the only method in PyTest.utils.


##
# Section V: Usage Patterns
##

# usage patterns:
#   complements doctest -- similar philosophy
#   replaces unittest
#   tests in situ
#   separate testing script
#   working with the PyTest module directly
#   using non-standard python installations

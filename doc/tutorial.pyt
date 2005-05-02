#!/usr/bin/env pytest
"""This script introduces pytest by explanation and example.
"""
# (c) 2005 Chad Whitacre <http://www.zetadev.com/>
# This program is beerware. If you like it, buy me a beer someday.
# No warranty is expressed or implied.


##
# TABLE OF CONTENTS
##

#   SECTION I: INTRODUCTION                         LINE  31
#
#   SECTION II: THE BASICS                          LINE  44
#
#   SECTION III: REAL WORLD EXAMPLES                LINE 114
#
#   SECTION IV: THE REPORT                          LINE 190
#
#   SECTION V: EXCEPTION HANDLING                   LINE 311
#
#   SECTION VI: USAGE PATTERNS                      LINE 395
#
#   SECTION VII: CONCLUSION                         LINE 419




##
# SECTION I: INTRODUCTION
##

# Pytest is a testing interpreter for Python. We call it an 'interpreter' rather
# than a 'framework' because tests written for pytest involve no framework
# besides the Python language itself. Pytests are regular Python scripts that
# are interpreted in a special way. This tutorial will explain and demonstrate
# how to take advantage of pytest's features and work around its faults.




##
# SECTION II: THE BASICS
##

# In general, testing involves three things:
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
#
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
# pytest interpreter. It could be run through the standard Python interpreter,
# but this probably wouldn't be very interesting, since test scripts generally
# don't do anything useful in and of themselves.




##
# SECTION III: REAL WORLD EXAMPLES
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
    def gobble(self, seq, i):
        for x in seq:
            if type(x) is type([]):
                self.gobble(x, i)
            elif x == i:
                self.yummy8s.append(x)
    gobble = classmethod(gobble)

ilove8s.gobble(mylist, 8)

len(ilove8s.yummy8s) == 3 # test


# Of course, what we *really* want to do is to build a fixture out of objects
# that are defined elsewhere. No problem. Here's a little test for whether the
# random module lives up to its name:

from sets import Set
from random import choice

foo = Set()
for i in range(10):
    foo.add(choice(range(10)))

len(foo) > 1 # test




##
# SECTION IV: THE REPORT
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
#
# For example, here's pytest's summary when executing this present script:

################################################################################
#                                 tutorial.pyt                                 #
################################################################################
#                                                                              #
#                                    passes:   10                              #
#                                  failures:    1                              #
#                                exceptions:    1                              #
#                             ----------------------                           #
#                               total tests:   12                              #
#                                                                              #
#                          other exceptions:    1                              #
#                                                                              #
#                              time elapsed:    0.3s                           #
#                                                                              #
################################################################################


# Pytest will also give you a detailed report for the following:
#
#   - Failed tests
#   - Tests that raised exceptions
#
# This detail report includes what the statement was, what line number it was
# on, the value of all relevant terms (for failures), and a traceback (for
# exceptions). For example, here is an exception:
"""
+------------------------------------------------------------------------------+
| EXCEPTION                     foo ( ) is True                     LINE:  323 |
+------------------------------------------------------------------------------+

Traceback (most recent call last):
  File "/usr/local/lib/python2.4/site-packages/PyTest/Observer.py", line 68, in
intercept
    if eval(statement, globals, locals):
  File "<string>", line 0, in ?
  File "<string>", line 66, in foo
Exception
"""

# If you look closely you will notice that the whitespace in the statement:
#
#   foo ( ) is True
#
# does not match the whitespace in our original statement:
#
#   foo() is True
#
# This is due to the way that pytest manipulates your script's source code to
# insert its testing framework, and in no way affects the actual execution of
# the code.
#
# You may also notice that the traceback looks a little goofy. Again, this is
# because of the way pytest interferes with the script's execution in order to
# gather its information; see the section below on exception handling for
# details.
#
# Apart from failures and exceptions, you can explicitly insert arbitrary
# information into the report using the print statement:

print 'hello world'
print >> sys.stdout, "(this works too)"


# The output of any print statements will appear in sequence in the report,
# along with the line number, etc., as with the exception above. However, as
# with exceptions, there are several gotchas:
#
#   - Currently pprint.pprint does not behave similarly. The workaround is to
#     use pformat:

from pprint import pprint, pformat
pprint("pprinted directly") # will be in the report, but not wrapped properly
print pformat(mylist) # will be in the report, properly wrapped


#   - Neither does sys.stdout.write; we may leave this one alone altogether to
#     allow for manual manipulation of the report on some level:

from os import linesep
sys.stdout.write('Anything written to stdout will appear in your report' +\
                 (linesep*3))


#   - Multi-line strings don't work. This is a bug. The workaround is to assign
#     to a variable, and then print the variable:

## print """
## this will break pytest
## """

foo = '''
but this won't
'''
print foo


# Pytest tries to be an objective observer of your code's execution, but as in
# science, absolute objectivity is hard to come by. As pytest gets more use I
# anticipate that these rough edges will be buffed away somewhat and that we
# will further approach this asymptote of objectivity.




##
# SECTION V: EXCEPTION HANDLING
##

# Exception handling in pytest is somewhat complex, due to the different
# execution contexts employed. All tests and print statements are executed in a
# "laboratory" context. Any exceptions they raise will be caught, tallied, and
# included in the final report. Execution of the script as a whole will then
# be allowed to proceed unhindered. Here's an example:

def foo():
    raise Exception

foo() is True # look for the traceback in the report


# Exceptions raised during print statements are also captured by pytest, tallied
# under 'other exceptions,' and included in the report. Execution then proceeds:

print foo()


# Fixture on the other hand, is run "as is," so exceptions raised by fixture are
# either caught very early or very late in pytest's execution cycle. In either
# case, they terminate execution of the script. If caught early -- e.g., a
# SyntaxError -- execution will terminate with no report being generated, and
# the standard traceback will be displayed on sys.stderr:

## mylist =


# If caught late, then the script must be rerun as if it were a standard Python
# script (i.e., without pytest's monitoring interferences) in order for a useful
# traceback to be gathered. Pytest does this for you, and since all output from
# test and print statements is already in the report buffer by the time the
# fixture exception is raised, the net effect of a late fixture exception is
# that all tests and print statements up to and including the terminal exception
# are included in the final report. The terminal exception is labeled "CRISIS."

def foo():
    raise Exception

## foo()


# However, there is a gotcha: when the script is rerun through the standard
# interpreter, any prior test or print exceptions are also re-triggered. So in
# fact, the terminal 'CRISIS' exception will be the first exception of any kind
# in the script, not necessarily the execution that triggered the re-execution.
# Aside from simply resolving exceptions in the order they occur, it is possible
# to work around this limitation by simply prefacing the fixture statement with
# a print statement. This will cause the exception to be captured and dealt with
# 'normally'.
#
# If you want to explicitly test whether some fixture raises a certain
# exception, you can use this idiom:

def foo():
    raise Exception

try:
    foo()
except:
    exc = sys.exc_info()[0]

exc is Exception # test


# The pytest package provides a utility class that has a convenience method
# called 'catch_exc' for this. This is currently the only method in
# pytest.utils:

from PyTest import utils

def foo(bar, baz):
    raise Exception

exc = utils.catch_exc(foo, 1, baz='bar')

exc is Exception # test




##
# SECTION VI: USAGE PATTERNS
##

# Pytest is intended as a simpler alternative to testing frameworks such as
# PyUnit (which is in the standard library as the unittest module), and Braham
# Cohen's testtest module, and as a complement to the standard library's doctest
# module, which is more about demonstrating common functionality than about
# complete test coverage. It shares doctest's philosophy of using already
# established patterns of interacting with Python to drive testing. In doctest's
# case this is the interpreter session. In pytest this is the script run through
# a command line interpreter.
#
# In addition to the expected pattern of recording test scripts in *.pyt files,
# and running them through the pytest interpreter, it would also be conceivable
# to include tests interspersed in an actual Python script itself. This would
# push the doctesting similarity even further, and could probably coexist with
# doctests. Furthermore, it is of course possible to use the PyTest module
# directly. For example, one could possibly write a pytest variant that would
# run traditional unittest tests as well.




##
# SECTION VII: CONCLUSION
##

# Pytest is currently in successful use on two projects. I release it in the
# hope that others will also find it valuable and will contribute to its
# development via feedback in the form of field test results, patches, etc.

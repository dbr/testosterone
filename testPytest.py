#!/usr/bin/env pytest
from pytest import utils

##
# the basics
##

# passing tests are silent; no output is reported
1+1==2

# a failing test produces output
1+1==3

# print statements also produce output
print 'hello world!'

# as do calls to pprint
from pprint import pprint
pprint('look ma! no burdensome framework!')

# in fact, all writes to stdout will be included in our report
sys.stdout.write('teehee!')


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


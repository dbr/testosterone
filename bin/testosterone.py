#!/usr/bin/env python
"""testosterone -- a manly Python test driver; man 1 testosterone for usage.
"""
import curses
import getopt
import os
import subprocess
import sys
import unittest
from StringIO import StringIO


WINDOWS = 'win' in sys.platform


# Basic API
# =========

def flatten(_suite):
    """Given a TestSuite, return a flattened TestSuite.
    """
    suite = unittest.TestSuite()
    for item in _suite:
        if isinstance(item, unittest.TestCase):
            suite.addTest(item)
        if isinstance(item, unittest.TestSuite):
            suite.addTests(flatten(item))
    return suite


def stat(base, run=True, recursive=True, stopwords=()):
    """Given a dotted module name, print statistics about its tests.

    The format of this function's output is:

        <name> <passing> <failures> <errors> <total>

    <passing> is given as a percentage; the other three are given in absolute
    terms. If run is False, then no statistics on passes, failures, and errors
    will be available, and the output for each will be a dash character ('-').
    run defaults to True. If recursive is False, then only the module explicitly
    named will be touched. If it is True (the default), then all sub-modules
    will also be included in the output, unless their name contains a stopword.

    """

    stats = []


    # Get modules.
    # ============

    modules = []

    module = __import__(base)
    for name in base.split('.')[1:]:
        module = getattr(module, name)
    modules.append(module)

    if recursive:
        path = os.path.dirname(module.__file__)
        for name in sorted(sys.modules):
            stop = False
            for word in stopwords:
                if word in name:
                    stop = True
            if stop:
                continue
            if not name.startswith(base):
                continue
            module = sys.modules[name]
            if module is None:
                continue
            if not module.__file__.startswith(path):
                # Skip external modules that ended up in our namespace.
                continue
            modules.append(module)


    # Write our output.
    # =================

    if run:
        runner = unittest.TextTestRunner(StringIO())
    for module in modules:
        suite = flatten(unittest.defaultTestLoader.loadTestsFromModule(module))
        pass5 = fail = err = '-'
        all = suite.countTestCases()
        if run:
            if all == 0:
                fail = err = 0
                pass5 = 100
            else:
                result = runner.run(suite)
                fail = len(result.failures)
                err = len(result.errors)
                pass5 =  int(round(((all - fail - err) / all)))
        print module.__name__, pass5, fail, err, all



# Main function a la Guido.
# =========================
# http://www.artima.com/weblogs/viewpost.jsp?thread=4829

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    if argv is None:

        argv = sys.argv
    try:
        try:
            short = "iInNrRg:"
            long_ = [ "interactive","scripted"
                    , "run","find"
                    , "recursive","flat"
                    , "ignore="
                     ]
            opts, args = getopt.getopt(argv[1:], short, long_)
        except getopt.error, msg:
            raise Usage(msg)


        interactive = True  # -i
        run = True          # -n
        recursive = True      # -r

        stopwords = []

        for opt, value in opts:
            if opt in ('-I', '--scripted'):
                interactive = False
            elif opt in ('-N', '--find'):
                find = False
            elif opt in ('-R', '--flat'):
                recursive = False
            elif opt in ('-g', '--ignore'):
                stopwords = value.split(',')

        if not args:
            raise Usage("No module named.")
        base = args[0]

        if WINDOWS or not interactive:
            stat(base, run, recursive, stopwords)
        else:
            CursesInterface(base)

    except Usage, err:
        print >> sys.stderr, err.msg
        print >> sys.stderr, __doc__
        return 2


if __name__ == "__main__":
    sys.exit(main())

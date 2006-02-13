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
            if name == modules[0].__name__:
                continue
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

    print "module".ljust(60), "pass", "fail", " err", " all"
    print "=" * 80

    tpass5 = tfail = terr = tall = '-'
    if run:
        tfail = terr = tall = 0
        runner = unittest.TextTestRunner(StringIO()) # swallow unittest output
    for module in modules:
        suite = flatten(unittest.defaultTestLoader.loadTestsFromModule(module))
        pass5 = fail = err = '-'
        all = suite.countTestCases()
        if run:
            if all != 0:
                result = runner.run(suite)
                fail = len(result.failures)
                err = len(result.errors)
                pass5 = (all - fail - err) / float(all)
                pass5 =  int(round(pass5*100))
                tfail += fail
                terr += err
                tall += all
        name = module.__name__.ljust(60)
        if pass5 == '-':
            pass5 = '  - '
        else:
            pass5 = str(pass5).rjust(3)+'%'
        fail = str(fail).rjust(4)
        err = str(err).rjust(4)
        all = str(all).rjust(4)

        print name, pass5, fail, err, all

    if tall:
        tpass5 = (tall - tfail - terr) / float(tall)
        tpass5 =  int(round(tpass5*100))
    if tpass5 == '-':
        tpass5 = '  - '
    else:
        tpass5 = str(tpass5).rjust(3)+'%'
    tfail = str(tfail).rjust(4)
    terr = str(terr).rjust(4)
    tall = str(tall).rjust(4)
    print "=" * 80
    print "TOTALS".ljust(60), tpass5, tfail, terr, tall

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

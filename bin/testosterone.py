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


__all__ = ('run', 'summarize')


WINDOWS = 'win' in sys.platform


# Helpers
# =======

class dev_null:
    """Output buffer that swallows everything.
    """
    def write(self, wheeeee):
        pass


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


# Basic API
# =========

def run(name_dotted):
    """Given a module dotted name, run that module's tests.
    """

    # Get a TestSuite.
    # ================

    module = __import__(name_dotted)
    for name in name_dotted.split('.')[1:]:
        module = getattr(module, name)
    suite = flatten(unittest.defaultTestLoader.loadTestsFromModule(module))


    # Run tests.
    # ==========
    # We want the test results on standard out, but not any of the program's
    # output.

    sys.stdout = dev_null()
    testout = StringIO()
    runner = unittest.TextTestRunner(testout)
    result = runner.run(suite)
    sys.stdout = sys.__stdout__
    print testout.getvalue()

    return (not result.wasSuccessful())


def summarize(base, quiet=True, recursive=True, run=True, stopwords=()):
    """Given a dotted module name, print statistics about its tests.

    The format of this function's output is:

        -------------<| testosterone |>-------------
        <header row>
        --------------------------------------------
        <name> <passing> <failures> <errors> <total>
        --------------------------------------------
        TOTALS <passing> <failures> <errors> <total>

    Boilerplate rows are actually 80 characters long, though. <passing> is given
    as a percentage (with a terminating percent sign); the other three are given
    in absolute terms. Data rows will be longer than 80 characters iff the field
    values exceed the following character lengths:

        name        60
        failures     4
        errors       4
        total        4

    If quiet is True (the default), then modules with no tests are not listed in
    the output; if False, they are. If recursive is False, then only the module
    explicitly named will be touched. If it is True (the default), then all
    sub-modules will also be included in the output, unless their name contains
    a stopword. If run is False, then no statistics on passes, failures, and
    errors will be available, and the output for each will be a dash character
    ('-'). run defaults to True.


    """

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
    # Capture stdout to prevent program output from cluttering up our report.

    out = StringIO()
    sys.stdout = dev_null()

    # Header
    c = '-'
    print >> out, c*31 + "<| testosterone |>" + c*31
    print >> out, "MODULE".ljust(60), "PASS", "FAIL", " ERR", " ALL"
    print >> out, c * 80

    # Data
    tpass5 = tfail = terr = tall = '-'
    tall = 0
    if run:
        tfail = terr = tall = 0
        runner = unittest.TextTestRunner(dev_null()) # swallow unittest output
    for module in modules:
        suite = flatten(unittest.defaultTestLoader.loadTestsFromModule(module))
        pass5 = fail = err = '-'
        all = suite.countTestCases()
        tall += all
        if not run:
            yes = True
        else:
            if all != 0:
                result = runner.run(suite)
                fail = len(result.failures)
                err = len(result.errors)
                pass5 = (all - fail - err) / float(all)
                pass5 =  int(round(pass5*100))
                tfail += fail
                terr += err

            has_result = (fail not in ('-', 0)) or (err not in ('-', 0))
            yes = (not quiet) or has_result

        name = module.__name__.ljust(60)
        if pass5 == '-':
            pass5 = '  - '
        else:
            pass5 = str(pass5).rjust(3)+'%'

        fail = str(fail).rjust(4)
        err = str(err).rjust(4)
        all = str(all).rjust(4)

        if yes:
            print >> out, name, pass5, fail, err, all

    # Footer
    if tall:
        if '-' not in (tfail, terr):
            tpass5 = (tall - tfail - terr) / float(tall)
            tpass5 =  int(round(tpass5*100))
    else:
        tfail = '-'
        terr = '-'
    if tpass5 == '-':
        tpass5 = '  - '
    else:
        tpass5 = str(tpass5).rjust(3)+'%'
    tfail = str(tfail).rjust(4)
    terr = str(terr).rjust(4)
    tall = str(tall).rjust(4)
    print >> out, c * 80
    print >> out, "TOTAL".ljust(60), tpass5, tfail, terr, tall


    # Restore stdout and output our report.
    # =====================================

    sys.stdout = sys.__stdout__
    print >> sys.stdout, out.getvalue()



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
            short = "g:iInNqQrRsS"
            long_ = [ "ignore="
                    , "interactive","scripted"
                    , "run","find"
                    , "recursive","flat"
                    , "quiet","verbose"
                    , "summary","detail"
                     ]
            opts, args = getopt.getopt(argv[1:], short, long_)
        except getopt.error, msg:
            raise Usage(msg)

        stopwords = []      # -g
        interactive = True  # -i
        run_ = True         # -n
        quiet = True        # -q
        recursive = True    # -r
        summary = True      # -s

        for opt, value in opts:
            if opt in ('-I', '--scripted'):
                interactive = False
            elif opt in ('-N', '--find'):
                run_ = False
            elif opt in ('-Q', '--verbose'):
                quiet = False
            elif opt in ('-R', '--flat'):
                recursive = False
            elif opt in ('-S', '--detail'):
                summary = False
            elif opt in ('-g', '--ignore'):
                stopwords = value.split(',')

        if not args:
            raise Usage("No module specified.")
        base = args[0]

        if WINDOWS or not interactive:
            if summary:
                summarize(base, quiet, recursive, run_, stopwords)
            else:
                run(base)
        else:
            CursesInterface(base)

    except Usage, err:
        print >> sys.stderr, err.msg
        print >> sys.stderr, "'man 1 testosterone' for instructions."
        return 2


if __name__ == "__main__":
    sys.exit(main())

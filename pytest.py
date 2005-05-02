#!/usr/bin/env python
"""Pytest is a testing interpreter for Python.

Usage:

    Pytest takes a single argument, which is a Unix filename pattern. Pytest
    will take all files in the current directory that match the pattern, and
    will run them through the main Python interpreter, monitoring their
    execution. Afterwards it will give you a report showing summary information
    and detailed information on any non-passing tests.


Examples:

    Test a single file, sending the report to your pager:

        $ pytest tutorial.pyt | less

    Test all files in the current directory with the .pyt extension:

        $ pytest '*.pyt'

    Remember to quote a pattern with special characters so that your shell does
    not expand it before pytest has a chance to.


For a detailed discussion of pytest, please see the file doc/tutorial.pyt
included with the distribution.

"""

##
# Set aside a clean testing environment.
##

import sys
__modules__ = sys.modules.copy()
# del __modules__['sys'] # afaict this doesn't actually unload the module :/
__globals__ = globals()
__locals__  = locals()



##
# Now proceed as normal.
##

import fnmatch
import os

import PyTest

##
# Set up some test runners.
##

def test_one(filename, report_buffer=None):

    """Given a filename, test and report on that single file.

    Only non-passing tests will be detailed in the report. An optional
    report_buffer may be passed in to capture the report output.

    """

    heisenberg = PyTest.Observer()
    heisenberg.start_timer()

    # read in the file to test and mix in our testing framework
    original = file(filename).read()
    interpolated = PyTest.Interpolator.interpolate(original)

    # set up the lab environment and run the test
    sys.modules = __modules__
    __globals__['__pytest__'] = sys.stdout = heisenberg
    heisenberg.run(filename, interpolated, __globals__, __locals__)

    heisenberg.stop_timer()

    if report_buffer is not None:
        # we are being run as part of a test suite, so send our report to
        # the main report buffer ...
        if (heisenberg.failures + heisenberg.exceptions) > 0:
            # but only if there is something to report
            sys.stdout = report_buffer
            heisenberg.report()
            sys.stdout = sys.__stdout__
        else:
            # nothing to report, so just be quiet
            pass
    else:
        # otherwise send the report to the standard output
        sys.stdout = sys.__stdout__
        heisenberg.report()

    return { 'passes'       : heisenberg.passes
           , 'failures'     : heisenberg.failures
           , 'exceptions'   : heisenberg.exceptions
           , 'nontest_excs' : heisenberg.nontest_excs
            }


def test_all(filenames):

    """Given a list of filenames, test and report on all the files.

    Only files with non-passing tests will be detailed in the report.

    """

    # determine the heading for our report
    if len(filenames) == 1:
        file_files = 'file'
    else:
        file_files = 'files'
    heading = 'EXECUTIVE SUMMARY: %s %s' % (len(filenames), file_files)

    # 'management' -- cause all it cares about is the executive summary
    management = PyTest.Observer()
    management.start_timer()

    for filename in filenames:

        results = test_one(filename, management)

        # update the executive summary
        management.passes += results['passes']
        management.failures += results['failures']
        management.exceptions += results['exceptions']
        management.nontest_excs += results['nontest_excs']

    management.stop_timer()
    management.report(heading)


if __name__ == '__main__':

    ##
    # Parse the command line argument.
    ##

    arg = sys.argv[1:2]
    if not arg:
        print __doc__
        raise SystemExit
    else:
        fnpattern = arg[0]
        filenames = fnmatch.filter(os.listdir('.'), fnpattern)


    ##
    # Pick and run a test runner.
    ##

    if len(filenames) == 0:
        print 'filename pattern did not match any files in the current directory'
        sys.exit(0)
    elif len(filenames) > 1:
        test_all(filenames)
    elif filenames[0] == fnpattern:
        test_one(filenames[0])
    else:
        test_all(filenames)

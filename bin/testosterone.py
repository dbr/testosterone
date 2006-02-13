#!/usr/bin/env python
"""This is a test runner for the httpy library.

Usage, e.g.:

    $ python bin/test.py site-packages/httpy/couplers

The argument to test.py is a path constraint. This runner looks for all tests/
directories under the path constraint, recursing into subdirectories. Within
those directories, it looks for files named test_*.py, and adds the return value
of test_suite within those files to its list of tests to run.

This really wants to have a RestartingTester that behaves like RestartingServer.
In fact, our test-finding code is very similar to our responder locating code in
the Multiple responder.


curses app

screen 1: ModulesScreen
    hierarchical list of modules for which tests are available, plus stats

    up/down -- change module selection
    pgup/pgdn -- change module selection by page
    home/end -- top and bottom of the list
    space -- toggle discrete/cumulative selection
    enter -- run tests and go to ResultsScreen
    F5 -- run tests and stay on ModulesScreen
    <ctrl>-F5 -- refresh list of modules
        do real work in child process, a la RestartingServer?
    <something> -- toggle show all/only fail/err


screen 2: ResultsScreen
    flat list of TestCases on left, grouped by failure/error, TextTestRunner
    output or interactive pdb session on right

    esc -- return to ModulesScreen
    up/down -- change TestCase selection; output follows selection
        so the output can be for
    F5 -- re-run current selection
    tab -- toggle between list and shell panes


Tests themselves should be run in a separate process that calls the same runner
in non-interactive mode. Spawning a new process on each "request" means we don't
have to worry about tracking module changes and restarting. We can just track
filesystem changes and rerun the module. After noticing a fs change, we should
wait a second or two in case any other quick changes happen (2 files saved, e.g.)


so how to build this up:
    non-interactive mode first


loading tests -> self.suites
    changes depending on test code
    account for both test cases being added and removed
running tests -> results
    changes depending on non-test code
drawing screen



class ModuleTests:
    "TestSuite subclass"

    direct = TestSuite
    cumulative = TestSuite





class TestManager:

    suites






"""
import curses
import getopt
import os
import sys
import unittest

import httpy


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


def gather(base):
    """Given a base module, crawl sys.modules looking for tests.

    Returns a dictionary: {'module dotted name': (<suite>, <suite>). The first
    suite contains tests from just that module. The second suite includes all
    the tests from that modules, and all tests from modules below that module.

    """

    if (not isinstance(base, basestring)) or ('.' in base):
        raise StandardError("base must be a non-dotted module name.")
    basemod = __import__(base)
    path = os.path.dirname(basemod.__file__)
    tests = {}

    for name in sorted(sys.modules):

        # Filter out unwanted modules.
        # ============================
        # _zope and jon are third-party modules bundled with httpy.

        if not name.startswith(base):
            continue
        if ('_zope' in name) or ('jon' in name):
            continue


        # Get a module and look for tests.
        # ================================

        module = sys.modules[name]
        if module is None:
            continue
        if not module.__file__.startswith(path):
            # Skip non-httpy modules that ended up in our namespace.
            continue
        suite = flatten(unittest.defaultTestLoader.loadTestsFromModule(module))
        if suite.countTestCases() == 0:
            continue


        # We have tests!
        # ==============
        # Store our tests, and add them to any ancestors' cumulative test
        # suites. Since we sorted sys.modules, ancestor will always be
        # populated first if it has tests. It might not have tests, though.

        below = flatten(unittest.TestSuite(suite))
        tests[name] = (suite, below)

        parts = name.split('.')[:-1]
        if not parts:
            continue
        for i in range(len(parts)):
            ancestor = '.'.join(parts[:i+1])
            if ancestor in tests:     # Ancestor already has its own tests too.
                tests[ancestor][1].addTests(suite._tests)
            else:                  # Ancestor doesn't have any of its own tests.
                empty = unittest.TestSuite()
                cumulative = unittest.TestSuite(suite._tests)
                tests[ancestor] = (empty, cumulative)

    return tests


def run(name, recursive=True):
    """Given a module dotted name, run its tests.

    If recursive is omitted or True, we run all tests below the named module. If
    False, we only run tests actually located in that module.

    """
    base = name
    if '.' in name:
        base = name.split('.')[0]
    tests = gather(base)
    for _name in tests:
        direct, cumulative = tests[_name]
        suite = direct
        if recursive:
           suite = cumulative
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    return (not result.wasSuccessful())


class CursesInterface:

    def __init__(self, base):
        self.suites = gather(base)
        self.numsuites = len(self.suites)
        self.base = base
        curses.wrapper(self.wrapme)
        os.system('clear')

    def wrapme(self, win):
        self.win = win
        curses.curs_set(0) # Don't show the cursor.
        screen = ModulesScreen(self)
        try:
            while 1:
                # Each screen returns the next screen.
                screen = screen.go()
        except KeyboardInterrupt:
            pass


class ModulesScreen:
    """Represents the main module listing.
    """

    win = None          # a curses window
    suites = {}         # a gather() dictionary
    numsuites = 0       # the number of suites gathered
    size = (0, 0)       # the size of the window
    viewrows = 0        # the number of rows in the viewport
    viewrow = 0         # the current row selected in the viewport
    cumulative = True   # direct or cumulative
    offset = 0          # the offset into self.suites.


    def __init__(self, iface):
        """Takes a CursesInterface object.
        """
        self.suites = iface.suites
        self.numsuites = iface.numsuites
        self.win = iface.win


    def go(self):
        """Interact with the user, return the next screen.
        """
        while 1:
            if self.size != self.win.getmaxyx():
                self.draw()

            c = self.win.getch()
            if c == ord('q'):
                raise KeyboardInterrupt
            elif c == ord('h'):
                pass # return HelpScreen(self.iface)

            elif c == curses.KEY_UP:
                if self.viewrow == 0:
                    if self.offset == 0:
                        curses.beep()
                        continue
                    self.offset -= 1
                    self.draw_list()
                    continue
                self.viewrow -= 1
                self.draw_list()

            elif c == curses.KEY_DOWN:
                if self.viewrow == self.viewrows:
                    if (self.offset+self.viewrows) == (self.numsuites-1):
                        curses.beep()
                        continue
                    self.offset += 1
                    self.draw_list()
                    continue
                if self.viewrow == self.numsuites-1:
                    curses.beep()
                    continue
                self.viewrow += 1
                self.draw_list()

            elif c == ord(' '):
                self.cumulative = not self.cumulative
                self.draw_list()

            elif c == curses.KEY_F5:
                result = unittest.TestResult()
                start = self.offset
                end = start + self.viewrows + 1
                suite = flatten(unittest.TestSuite(self.suites[start:end]))
                suite.run(result)
                self.result = result
                self.draw_list()


    def run(self, start, end):
        """Run tests.
        """


    def draw(self):
        """Draw the screen.
        """

        # Get window dimensions; account for border.
        # ==========================================

        self.win.clear()
        self.win.refresh()
        self.size = tuple([i-1 for i in self.win.getmaxyx()])
        H, W = self.size
        c1h = c2h = c3h = H - 7
        c2w = c3w = 16
        c1w = W - c2w - c3w - 4
        self.c1 = (c1h, c1w)
        self.c2 = (c2h, c2w)
        self.c3 = (c3h, c3w)


        # Background, border, scrollbar
        # =============================

        self.win.bkgd(' ')
        self.win.border()

        # banner bottom border
        self.win.addch(2,0,curses.ACS_LTEE)
        for i in range(0,W-1):
            self.win.addch(2,i+1,curses.ACS_HLINE)
        self.win.addch(2,W,curses.ACS_RTEE)

        # main headers bottom border
        self.win.addch(4,0,curses.ACS_LTEE)
        for i in range(0,W-1):
            self.win.addch(4,i+1,curses.ACS_HLINE)
        self.win.addch(4,W,curses.ACS_RTEE)

        # secondary headers bottom border
        self.win.addch(6,0,curses.ACS_LTEE)
        for i in range(0,W-1):
            self.win.addch(6,i+1,curses.ACS_HLINE)
        self.win.addch(6,W,curses.ACS_RTEE)

        # column 1 right border
        self.win.addch(2,(c1w+2),curses.ACS_TTEE)
        self.win.vline(3,(c1w+2),curses.ACS_VLINE,H-3)
        self.win.addch(4,(c1w+2),curses.ACS_PLUS)
        self.win.addch(6,(c1w+2),curses.ACS_PLUS)
        self.win.addch(H,(c1w+2),curses.ACS_BTEE)

        # column 2 right border
        self.win.addch(2,(c1w+c2w+3),curses.ACS_TTEE)
        self.win.vline(3,(c1w+c2w+3),curses.ACS_VLINE,H-3)
        self.win.addch(4,(c1w+c2w+3),curses.ACS_PLUS)
        self.win.addch(6,(c1w+c2w+3),curses.ACS_PLUS)
        self.win.addch(H,(c1w+c2w+3),curses.ACS_BTEE)

        # scrollbar
        #self.win.setscrreg(7,H)
        #for i in range(7,H):
        #   self.win.addch(i,(c1w+c2w+c3w+4),curses.ACS_CKBOARD)


        # Banner text and column headers
        # ==============================

        banner = "testosterone -- the manly Python test driver"
        self.win.addstr(1,2,banner)

        self.win.addstr(3,2,"modules")
        self.win.addstr(3,c1w+7,"discrete")
        self.win.addstr(3,c1w+c2w+7,"cumulative")

        self.win.addstr(5,c1w+4,"fail")
        self.win.addstr(5,c1w+4+6,"err")
        self.win.addstr(5,c1w+4+11,"all")

        self.win.addstr(5,c1w+4+c2w+1,"fail")
        self.win.addstr(5,c1w+4+c2w+1+6,"err")
        self.win.addstr(5,c1w+4+c2w+1+11,"all")


        # Module listing
        # ==============
        # This calls self.win.refresh()

        self.draw_list()



    def draw_list(self):
        """Draw the list of modules.
        """

        c1h, c1w = self.c1
        c2h, c2w = self.c2
        c3h, c3w = self.c3

        self.viewrows = c1h-1

        i = 7
        start = self.offset
        end = start + self.viewrows + 1
        prefix = '' # signal for cumulative bullets

        for name in sorted(self.suites)[start:end]:

            # Short name
            # ==========

            parts = name.split('.')
            shortname = ('  '*(len(parts)-1)) + parts[-1]
            if len(shortname) > c1w:
                shortname = shortname[:3] + '...'
            shortname = shortname.ljust(c1w)
            self.win.addstr(i,2,shortname)


            # Bullet(s)
            # =========

            l = ' '
            r = ' '
            if i == self.viewrow + 7:
                if self.cumulative and not prefix:
                    prefix = name
                l = curses.ACS_RARROW
                r = curses.ACS_LARROW
            elif self.cumulative and prefix and name.startswith(prefix):
                l = r = curses.ACS_BULLET
            self.win.addch(i,1,l)
            self.win.addch(i,self.size[1]-1,r)


            # Discrete tests
            # ==============

            suite, below = self.suites[name]

            err = '- '
            fail = '- '
            num = suite.countTestCases()
            if num > 9999:
                num = 9999
            self.win.addstr(i,c1w+4,str(err).rjust(4))
            self.win.addstr(i,c1w+4+5,str(fail).rjust(4))
            self.win.addstr(i,c1w+4+10,str(num).rjust(4))


            # Cumulative tests
            # ================

            cerr = '- '
            cfail = '- '
            cnum = below.countTestCases()
            if num > 9999:
                num = 9999
            self.win.addstr(i,c1w+4+c2w+1,str(cerr).rjust(4))
            self.win.addstr(i,c1w+4+c2w+1+5,str(cfail).rjust(4))
            self.win.addstr(i,c1w+4+c2w+1+10,str(cnum).rjust(4))


            i += 1
            if i > self.viewrows+7:
                break


        # Continuation indicators
        # =======================

        if start > 0:
            c = curses.ACS_UARROW
        else:
            c = curses.ACS_HLINE
        self.win.addch(6,1,c)
        self.win.addch(6,self.size[1]-1,c)

        if end < self.numsuites:
            c = curses.ACS_LANTERN
        else:
            c = curses.ACS_HLINE
        self.win.addch(self.size[0],1,c)
        self.win.addch(self.size[0],self.size[1]-1,c)


        # Distinct/Cumulative
        # ===================

        W = self.size[1]
        if self.cumulative:
            self.win.addstr(3,c1w+7,"discrete")
            self.win.addstr(3,c1w+c2w+7,"cumulative", curses.A_BOLD)
        else:
            self.win.addstr(3,c1w+7,"discrete", curses.A_BOLD)
            self.win.addstr(3,c1w+c2w+7,"cumulative")


        # Finally, draw the window.
        # =========================

        self.win.refresh()



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
            opts, args = getopt.getopt(argv[1:], "hi", ["help", ""])
        except getopt.error, msg:
            raise Usage(msg)

        if ('-i','') in opts:
            CursesInterface('httpy')
        else:
            name = 'httpy'
            if args:
                name = args[0]
            run(name)

    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2


if __name__ == "__main__":
    sys.exit(main())




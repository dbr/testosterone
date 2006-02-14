#!/usr/bin/env python
"""testosterone -- a manly Python test driver; man 1 testosterone for usage.
"""
import Queue
import curses
import getopt
import logging
import os
import subprocess
import sys
import threading
import time
import traceback
import unittest
from StringIO import StringIO

__all__ = ("detail", "summarize")
__author__ = "Chad Whitacre <chad@zetaweb.com>"
__version__ = "0.4"


format = "%(name)-16s %(levelname)-8s %(message)s"
format = "%(levelname)-8s %(message)s"
logging.basicConfig( filename='log'
                   , level=logging.DEBUG
                   , format=format
                    )
logger = logging.getLogger('testosterone')


# Helpers
# =======

C = '-'
BANNER = C*31 + "<| testosterone |>" + C*31
BORDER = C * 80
HEADERS = ' '.join(["MODULE".ljust(60), "PASS", "FAIL", " ERR", " ALL"])
WINDOWS = 'win' in sys.platform

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

def detail(name_dotted):
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
    # We only write our report to stdout after the tests have been run. This is
    # necessary because we don't want to clutter the report with an program
    # output and/or pdb sessions.

    out = StringIO()
    runner = unittest.TextTestRunner(out)
    result = runner.run(suite)
    print BANNER
    print out.getvalue()

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
    submodules will also be included in the output, unless their name contains a
    stopword. If run is False, then no statistics on passes, failures, and
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
                if word and word in name:
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
    # Divert testing output to prevent program output and pdb sessions from
    # cluttering up our report.

    out = StringIO()

    # Header
    print >> out, BANNER
    print >> out, HEADERS
    print >> out, BORDER

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
    print >> out, BORDER
    print >> out, "TOTAL".ljust(60), tpass5, tfail, terr, tall


    # Output our report.
    # ==================

    sys.stdout.write(out.getvalue())




# Inter-process communicators.
# ============================

class Summary:
    """Represent the data from an inter-process summarize() call.
    """

    data = {}   # a dictionary, {name: 4-tuple}
    total = []  # a single 4-tuple
    names = []  # a list of modules names in data

    def __init__(self, stopwords=()):
        """Takes a dotted name, a list, and two booleans.
        """
        self.stopwords = stopwords
        self.data = {}
        self.total = []

    def __getitem__(self, key):
        return self.data[key]

    def __len__(self):
        return self.data.__len__()

    def __iter__(self):
        return self.data.__iter__()
    iterkeys = __iter__


    def refresh(self, base, run=False):
        """Update our information.
        """
        call = ( sys.executable
               , sys.argv[0]
               , '--stopwords=%s' % ','.join(self.stopwords)
               , run and '--run' or '--find'
               , '--scripted'
               , '--summary'
               , '--verbose' # always verbose; deal with empties higher up
               , base
                )
        #open('log', 'a+').write(' '.join(call)+'\n')
        proc = subprocess.Popen(call, stdout=subprocess.PIPE)
        lines = proc.stdout.read().splitlines()
        self.total = lines[-1].split()[1:]
        del lines[-1]
        start = False
        for line in lines:
            line = line.strip('\n')
            if line == BANNER:
                start = True
                continue
            if (not start) or (not line) or line in (HEADERS, BORDER):
                continue
            tokens = line.split()
            self.data[tokens[0]] = tokens[1:]
        self.names = sorted(self.data)


if '--foo' in sys.argv:
    foo = Summary(('_zope','jon'))
    foo.refresh('httpy')
    import pdb; pdb.set_trace()
    raise SystemExit



# Interactive interface
# =====================

class CursesInterface:

    def __init__(self, base, stopwords):
        self.base = base
        self.stopwords = stopwords
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


class Spinner:
    """Represent a random work indicator, handled in a separate thread.
    """

    def __init__(self, spin):
        """Takes a callable that actually draws/undraws the spinner.
        """
        self.spin = spin
        self.flag = Queue.Queue(1)

    def start(self):
        """Show a spinner.
        """
        self.thread = threading.Thread(target=self.spin)
        self.thread.start()

    def stop(self):
        """Stop the spinner.
        """
        self.flag.put(True)
        self.thread.join()

    def wrap(self, call, *args, **kwargs):
        """Convenient way to run a routine with a spinner.
        """
        self.start()
        call(*args, **kwargs)
        self.stop()


class ModulesScreen:
    """Represents the main module listing.

    UI-driven events:

        F5 -- refresh list of modules, resetting tests to un-run
        space -- run tests for selected module and submodules
        enter -- run selection

    """

    H = W = 0       # the dimensions of the window
    banner = " testosterone " # shows up at the top
    selected = ''   # the dotted name of the currently selected item
    start = end = 0 # the current index positions in summary
    summary = {}    # a data dictionary per summarize()
    toprows = 3     # the number of boilerplate rows at the top
    viewrow = 0     # the current row selected in the viewport
    viewrows = 0    # the number of rows in the viewport
    win = None      # a curses window


    def __init__(self, iface):
        """Takes a CursesInterface object.
        """
        self.win = iface.win
        self.base = iface.base
        self.stopwords = iface.stopwords
        self.spinner = Spinner(self.spin)
        self.summary = Summary(self.stopwords)
        self.summary.refresh(self.base)
        self.selected = self.summary.names[self.start]

    def reload(self):
        self.summary = Summary(self.stopwords)
        self.spinner.wrap(self.summary.refresh, self.base)

    def get_size(self):
        """getmaxyx is 1-indexed, but just about everything else is 0-indexed.
        """
        return tuple([i-1 for i in self.win.getmaxyx()])

    def go(self):
        """Interact with the user, return the next screen.
        """

        while 1:

            # Draw the screen.
            # ================
            # But first make sure the terminal is big enough.

            if (self.H, self.W) != self.get_size():
                self.win.clear()
                self.win.refresh()
                self.H, self.W = self.get_size()
                if (self.H < 4) or (self.W < 34):
                    msg = "Terminal too small."
                    if (self.H == 0) or (self.W < len(msg)):
                        continue
                    self.win.addstr(self.H/2,(self.W-len(msg))/2,msg)
                    self.win.refresh()
                    continue
                self.draw()


            # Trap a key.
            # ===========

            c = self.win.getch()

            if c == ord('q'):
                raise KeyboardInterrupt

            elif c == ord('h'):
                pass # return HelpScreen(self.iface)

            elif c == curses.KEY_UP:
                if self.viewrow == 0:
                    if self.start == 0:
                        curses.beep()
                        continue
                    self.start -= 1
                    self.draw_list()
                    continue
                self.viewrow -= 1
                self.draw_list()

            elif c == curses.KEY_DOWN:
                numrows = len(self.summary)
                if self.viewrow == self.viewrows:
                    if (self.start+self.viewrows) == numrows-1:
                        curses.beep()
                        continue
                    self.start += 1
                    self.draw_list()
                    continue
                if self.viewrow == numrows:
                    curses.beep()
                    continue
                self.viewrow += 1
                self.draw_list()

            elif c == curses.KEY_F5:
                self.reload()
                self.draw_list()

            elif c == ord(' '):
                self.spinner.wrap(self.summary.refresh,self.selected, run=True)
                self.draw_list()


    def spin(self):
        """Put a 'working' indicator in the banner.
        """
        l = (self.W - len(self.banner)) / 2
        stop = False
        while not stop:
            for i in range(6):
                spun = " working%s " % ('.'*i).ljust(5)
                self.win.addstr(0,l,spun)
                self.win.refresh()
                try:
                    stop = self.spinner.flag.get(timeout=0.1)
                except Queue.Empty:
                    pass
        self.draw_banner()


    def draw_banner(self):
        l = (self.W - len(self.banner)) / 2
        self.win.addstr(0,l,self.banner)


    def draw(self):
        """Draw the screen.
        """

        # Get window dimensions; account for border.
        # ==========================================

        H,W = self.H,self.W
        c1h = c2h = H - self.toprows
        c2w = 20
        c1w = W - c2w - 7
        self.c1 = (c1h, c1w)
        self.c2 = (c2h, c2w)


        # Background, border, scrollbar
        # =============================

        self.win.bkgd(' ')
        self.win.border()

        # headers bottom border
        self.win.addch(2,0,curses.ACS_LTEE)
        for i in range(0,W-1):
            self.win.addch(2,i+1,curses.ACS_HLINE)
        self.win.addch(2,W,curses.ACS_RTEE)

        # column border
        self.win.addch(0,(W-c2w-3),curses.ACS_TTEE)
        self.win.vline(1,(W-c2w-3),curses.ACS_VLINE,H-1)
        self.win.addch(2,(W-c2w-3),curses.ACS_PLUS)
        self.win.addch(H,(W-c2w-3),curses.ACS_BTEE)


        # Banner text and column headers
        # ==============================

        banner = " testosterone "
        l = (W - len(banner)) / 2
        r = l + len(banner)
        self.win.addch(0,l-2,curses.ACS_LARROW)
        self.win.addch(0,l-1,curses.ACS_VLINE)
        self.win.addstr(0,l,banner)
        self.win.addch(0,r,curses.ACS_VLINE)
        self.win.addch(0,r+1,curses.ACS_RARROW)

        self.win.addstr(1,3,"MODULES")
        self.win.addstr(1,self.W-c2w-1,"PASS")
        self.win.addstr(1,self.W-c2w-1+5,"FAIL")
        self.win.addstr(1,self.W-c2w-1+10," ERR")
        self.win.addstr(1,self.W-c2w-1+15," ALL")


        # Module listing
        # ==============
        # This calls self.win.refresh()

        self.draw_list()



    def draw_list(self):
        """Draw the list of modules.
        """

        c1h, c1w = self.c1
        c2h, c2w = self.c2

        self.viewrows = c1h-1
        self.end = self.start + self.viewrows + 1


        # Current selection
        # =================
        # Eventually I would maybe like to see this go in a message area at
        # the bottom.

        self.selected = self.summary.names[self.start+self.viewrow]
        #selected = self.selected
        #if len(self.selected) > self.W-17:
        #    selected = self.selected[:self.W-20]+'...'
        #self.win.addstr(1,13,selected.ljust(self.W-17))


        i = self.toprows
        prefix = '' # signal for submodule bullets

        for name in self.summary.names[self.start:self.end]:

            # Short name
            # ==========

            parts = name.split('.')
            shortname = ('  '*(len(parts)-1)) + parts[-1]
            if len(shortname) > c1w:
                shortname = shortname[:c1w-3] + '...'
            shortname = shortname.ljust(c1w)
            self.win.addstr(i,3,shortname)


            # Bullet(s)
            # =========

            l = ' '
            r = ' '
            if i == self.viewrow + self.toprows:
                if not prefix:
                    prefix = name
                l = curses.ACS_RARROW
                r = curses.ACS_LARROW
            elif prefix and name.startswith(prefix):
                l = r = curses.ACS_BULLET
            self.win.addch(i,1,l)
            self.win.addch(i,self.W-1,r)


            # Data
            # ====

            try:
                pass5, fail, err, all = self.summary[name]
            except:
                raise StandardError(self.summary[name])
            if pass5 == '-':
                pass5 = '- '
            if len(fail) > 4:
                fail = '9999'
            if len(err) > 4:
                err = '9999'
            if len(all) > 4:
                all = '9999'
            self.win.addstr(i,self.W-c2w-1,pass5.rjust(4))
            self.win.addstr(i,self.W-c2w-1+5,err.rjust(4))
            self.win.addstr(i,self.W-c2w-1+10,fail.rjust(4))
            self.win.addstr(i,self.W-c2w-1+15,all.rjust(4))

            i += 1
            if i > self.viewrows + self.toprows:
                break


        # Continuation indicators
        # =======================

        if self.start > 0:
            c = curses.ACS_UARROW
        else:
            c = curses.ACS_HLINE
        self.win.addch(2,1,c)
        self.win.addch(2,self.W-1,c)

        if self.end < len(self.summary):
            c = curses.ACS_LANTERN
        else:
            c = curses.ACS_HLINE
        self.win.addch(self.H,1,c)
        self.win.addch(self.H,self.W-1,c)


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
            short = "iInNqQrRsSx:"
            long_ = [ "interactive","scripted"
                    , "run","find"
                    , "quiet","verbose"
                    , "recursive","flat"
                    , "summary","detail"
                    , "stopwords="
                     ]
            opts, args = getopt.getopt(argv[1:], short, long_)
        except getopt.error, msg:
            raise Usage(msg)

        interactive = True  # -i
        run = True          # -n
        quiet = True        # -q
        recursive = True    # -r
        summary = True      # -s
        stopwords = []      # -x

        for opt, value in opts:
            if opt in ('-I', '--scripted'):
                interactive = False
            elif opt in ('-N', '--find'):
                run = False
            elif opt in ('-Q', '--verbose'):
                quiet = False
            elif opt in ('-R', '--flat'):
                recursive = False
            elif opt in ('-S', '--detail'):
                summary = False
            elif opt in ('-x', '--stopwords'):
                stopwords = value.split(',')

        if not args:
            raise Usage("No module specified.")
        base = args[0]

        if WINDOWS or not interactive:
            if summary:
                summarize(base, quiet, recursive, run, stopwords)
            else:
                detail(base, stopwords)
        else:
            CursesInterface(base, stopwords)

    except Usage, err:
        print >> sys.stderr, err.msg
        print >> sys.stderr, "'man 1 testosterone' for instructions."
        return 2


if __name__ == "__main__":
    sys.exit(main())

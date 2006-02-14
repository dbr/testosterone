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

    data = []   # a dictionary, {name:<6-tuples>}:
                #   0-3 summarize() data: pass5, fail, err, all
                #   4   bool; whether to show this item
                #   5   None/False/True; whether the data is recent
    totals = () # a single 4-tuple per summarize()
    names = []  # a list of names for which show is True

    def __init__(self, stopwords=()):
        """Takes a dotted name, a list, and two booleans.
        """
        self.stopwords = stopwords
        self.data = {}
        self.total = []
        self.names = []

    def __getitem__(self, key):
        return self.data[key]

    def __len__(self):
        """Only count items for which show is True.
        """
        return len([v for v in self.data.values() if v[4]])

    def __iter__(self):
        return self.data.__iter__()
    iterkeys = __iter__


    def refresh(self, base, run=False):
        """Update our information.
        """

        # Mark currently fresh data as stale.
        # ===================================

        for name, datum in self.data.iteritems():
            if datum[5] is True:
                datum[5] = False


        # Make the call.
        # ==============

        call = ( sys.executable
               , sys.argv[0]
               , '--stopwords=%s' % ','.join(self.stopwords)
               , run and '--run' or '--find'
               , '--scripted'
               , '--summary'
               , '--verbose' # always verbose; deal with empties higher up
               , base
                )
        proc = subprocess.Popen(call, stdout=subprocess.PIPE)
        logger.debug(' '.join(call))


        # Total
        # =====

        lines = proc.stdout.read().splitlines()
        self.totals = lines[-1].split()[1:]
        del lines[-1]


        # Data
        # ====
        # Besides our own formatting, we also need to ignore any program output
        # that preceded our report.

        start = False
        for line in lines:

            # Decide if we want this line, and if so, split it on spaces.
            # ===========================================================

            line = line.strip('\n')
            if line == BANNER:
                start = True
                continue
            if (not start) or (not line) or line in (HEADERS, BORDER):
                continue
            tokens = line.split()


            # Convert the row to our record format.
            # =====================================
            # The tricky part is deciding whether to show this row: we want to
            # list modules that have non-passing tests, or that have submodules
            # with non-passing tests. Since data is coming to us ordered, we
            # can count on ancestor modules already being in self.data by the
            # time we get to a module with non-passing tests.

            name = tokens[0]
            stats = tokens[1:]

            has_tests = int(stats[3]) > 0

            fresh = None
            if has_tests and ('-' not in stats):
                fresh = True

            show = False
            if has_tests and (stats[0] != '100%'):
                show = True
                parts = name.split('.')[:-1]
                for i in range(len(parts),0,-1):
                    _name = '.'.join(parts[:i])
                    self.data[_name][4] = True

            self.data[name] = stats + [show, fresh]


        # Store a sorted list of our keys.
        # ================================

        self.names = sorted([n for n in self.data if self.data[n][4]])


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

        # colors
        bg = curses.COLOR_BLACK
        curses.init_pair(1, curses.COLOR_WHITE, bg)
        curses.init_pair(2, curses.COLOR_RED, bg)
        curses.init_pair(3, curses.COLOR_GREEN, bg)
        curses.init_pair(4, curses.COLOR_CYAN, bg)

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

    def __call__(self, call, *args, **kwargs):
        """Convenient way to run a routine with a spinner.
        """
        self.start()
        call(*args, **kwargs)
        self.stop()


class DoneScrolling(StandardError):
    """Represents the edge of a scrolling area.
    """


class ModulesScreen:
    """Represents the main module listing.

    UI-driven events:

        F5 -- refresh list of modules, resetting tests to un-run
        space -- run tests for selected module and submodules
        enter -- run selection

    """

    H = W = 0       # the dimensions of the window
    banner = " testosterone " # shows up at the top
    bottomrows = 3  # the number of boilerplate rows at the bottom
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
        self.spinner(self.summary.refresh, self.base)

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
            # The first couple exit early, the rest want to redraw the list.

            c = self.win.getch()

            if c == ord('q'):
                raise KeyboardInterrupt
            elif c == ord('h'):
                continue # return HelpScreen(self.iface)

            if c == curses.KEY_UP:    # up
                self.scroll(1)
            elif c == curses.KEY_DOWN:  # down
                self.scroll(-1)
            elif c == curses.KEY_NPAGE: # page up
                self.scroll(-(self.viewrows*2)-1)
                self.viewrow = 0
            elif c == curses.KEY_PPAGE: # page down
                self.scroll((self.viewrows*2)-1)
                self.viewrow = 0
            elif c == curses.KEY_F5:    # F5
                self.reload()
            elif c == ord(' '):
                self.spinner(self.summary.refresh, self.selected, run=True)
            self.draw_list()


    def scroll_one(self, down=False):
        """Scroll the viewport up by one row, or down if down is True.
        """

        up = not down
        numrows = len(self.summary)-1

        if up: # scroll up
            if self.viewrow == 0: # top of viewport
                if self.start == 0: # top of list
                    raise DoneScrolling
                else: # not top of list
                    self.start -= 1
            else: # not top of viewport
                self.viewrow -= 1

        elif down: # scroll down
            if self.viewrow == numrows: # bottom of list
                raise DoneScrolling
            else: # not bottom of list
                if self.viewrow == self.viewrows: # bottom of viewport
                    self.start += 1
                else: # not bottom of viewport
                    self.viewrow += 1

        ints = self.viewrow, self.viewrows, self.start, numrows
        logger.debug(' '.join([str(i) for i in ints]))


    def scroll(self, delta):
        """Viewport scrolling.
        """
        down = delta < 0
        delta = abs(delta)
        try:
            for i in range(delta):
                self.scroll_one(down)
        except DoneScrolling:
            curses.beep()


    def spin(self):
        """Put a 'working' indicator in the banner.
        """
        l = (self.W - len(self.banner)) / 2
        stop = False
        while not stop:
            for i in range(4):
                spun = "  working%s  " % ('.'*i).ljust(3)
                self.win.addstr(0,l,spun,curses.A_BOLD)
                self.win.refresh()
                try:
                    stop = self.spinner.flag.get(timeout=0.25)
                except Queue.Empty:
                    pass
        self.draw_banner()


    def draw_banner(self):
        l = (self.W - len(self.banner)) / 2
        self.win.addstr(0,l,self.banner,curses.A_BOLD)


    def draw(self):
        """Draw the screen.
        """

        # Get window dimensions; account for border.
        # ==========================================

        H,W = self.H,self.W
        c1h = c2h = H - self.toprows - self.bottomrows
        c2w = 20
        c1w = W - c2w - 7
        self.c1 = (c1h, c1w)
        self.c2 = (c2h, c2w)
        self.viewrows = c1h


        # Background and border
        # =====================

        bold = curses.A_BOLD

        self.win.bkgd(' ')
        self.win.border() # not sure how to make this A_BOLD
        self.win.addch(0,0,curses.ACS_ULCORNER,bold)
        self.win.addch(0,W,curses.ACS_URCORNER,bold)
        self.win.addch(H,0,curses.ACS_LLCORNER,bold)
        #self.win.addch(H,W,curses.ACS_LRCORNER,bold) error! why?
        for i in range(1,W):
            self.win.addch(0,i,curses.ACS_HLINE,bold)
            self.win.addch(H,i,curses.ACS_HLINE,bold)
        for i in range(1,H):
            self.win.addch(i,0,curses.ACS_VLINE,bold)
            self.win.addch(i,W,curses.ACS_VLINE,bold)

        # headers bottom border
        self.win.addch(2,0,curses.ACS_LTEE,bold)
        for i in range(0,W-1):
            self.win.addch(2,i+1,curses.ACS_HLINE,bold)
        self.win.addch(2,W,curses.ACS_RTEE,bold)

        # footer top border
        self.win.addch(H-2,0,curses.ACS_LTEE,bold)
        for i in range(0,W-1):
            self.win.addch(H-2,i+1,curses.ACS_HLINE,bold)
        self.win.addch(H-2,W,curses.ACS_RTEE,bold)

        # column border
        bw = (W-c2w-3)
        self.win.addch(0,bw,curses.ACS_TTEE,bold)
        self.win.vline(1,bw,curses.ACS_VLINE,H-1,bold)
        self.win.addch(2,bw,curses.ACS_PLUS,bold)
        self.win.addch(H-2,bw,curses.ACS_PLUS,bold)
        self.win.addch(H,bw,curses.ACS_BTEE,bold)


        # Banner text and column headers
        # ==============================

        banner = " testosterone "
        l = (W - len(banner)) / 2
        r = l + len(banner)
        self.win.addch(0,l-2,curses.ACS_LARROW,bold)
        self.win.addch(0,l-1,curses.ACS_VLINE,bold)
        self.win.addstr(0,l,banner,bold)
        self.win.addch(0,r,curses.ACS_VLINE,bold)
        self.win.addch(0,r+1,curses.ACS_RARROW,bold)

        self.win.addstr(1,3,"MODULES",bold)
        self.win.addstr(1,self.W-c2w-1,"PASS",bold)
        self.win.addstr(1,self.W-c2w-1+5,"FAIL",bold)
        self.win.addstr(1,self.W-c2w-1+10," ERR",bold)
        self.win.addstr(1,self.W-c2w-1+15," ALL",bold)


        # Module listing
        # ==============
        # This calls self.win.refresh()

        self.draw_list()



    def draw_list(self):
        """Draw the list of modules.
        """

        c1h, c1w = self.c1
        c2h, c2w = self.c2

        # erase current listing
        for i in range(self.toprows+1, self.viewrows+self.toprows):
            self.win.addstr(i,1,' '*(c1w+2))
            self.win.addstr(i,c1w+5,' '*(c2w+2))

        prefix = '' # signal for submodule bullets
        displayed = []
        rownum = 0  # the row we are currently outputting
        self.end = self.start + self.viewrows + 1

        for i in range(self.start, self.end):

            name = self.summary.names[i]
            rownum = self.toprows + i - self.start

            ints = (self.start, self.end, rownum)
            logger.debug(' '.join([str(i) for i in ints]))

            pass5, fail, err, all, show, fresh = self.summary[name]

            displayed.append(name) # helps determine self.selected


            # Determine highlighting for this row.
            # ====================================

            has_tests = int(all) > 0

            if fresh is None and not has_tests:
                color = curses.color_pair(1)|curses.A_DIM
            elif fresh is None and has_tests:
                color = curses.color_pair(1)|curses.A_BOLD
            elif fresh is False:
                color = curses.color_pair(2)|curses.A_DIM
            elif fresh is True:
                color = curses.color_pair(2)|curses.A_BOLD


            # Short name, with indent.
            # ========================

            parts = name.split('.')
            shortname = ('  '*(len(parts)-1)) + parts[-1]
            if len(shortname) > c1w:
                shortname = shortname[:c1w-3] + '...'
            shortname = shortname.ljust(c1w)
            self.win.addstr(rownum,3,shortname,color)


            # Bullet(s)
            # =========

            l = ' '
            r = ' '
            a = curses.color_pair(3)|curses.A_BOLD
            if i == self.viewrow+self.toprows:
                if not prefix:
                    prefix = name
                l = curses.ACS_RARROW
                r = curses.ACS_LARROW
            elif prefix and name.startswith(prefix):
                l = r = curses.ACS_BULLET
            self.win.addch(rownum,1,l,a)
            self.win.addch(rownum,self.W-1,r,a)


            # Data
            # ====

            if pass5 == '-':
                pass5 = '- '
            if len(fail) > 4:
                fail = '9999'
            if len(err) > 4:
                err = '9999'
            if len(all) > 4:
                all = '9999'

            w = self.W-c2w-1
            self.win.addstr(rownum,w,pass5.rjust(4),color)
            self.win.addstr(rownum,w+5,err.rjust(4),color)
            self.win.addstr(rownum,w+10,fail.rjust(4),color)
            self.win.addstr(rownum,w+15,all.rjust(4),color)

            if i > len(self.summary)+1:
                break

        self.selected = displayed[self.viewrow]


        # Continuation indicators
        # =======================

        if self.start > 0:
            c = curses.ACS_UARROW
        else:
            c = curses.ACS_HLINE
        self.win.addch(2,1,c,curses.A_BOLD)
        self.win.addch(2,self.W-1,c,curses.A_BOLD)

        if self.end < len(self.summary):
            c = curses.ACS_LANTERN
        else:
            c = curses.ACS_HLINE
        self.win.addch(self.H,1,c,curses.A_BOLD)
        self.win.addch(self.H,self.W-1,c,curses.A_BOLD)


        # Totals
        # ======

        color = curses.color_pair(4)|curses.A_BOLD

        tpass5, tfail, terr, tall = self.summary.totals
        if tpass5 == '-':
            tpass5 = '- '
        if len(tfail) > 4:
            tfail = '9999'
        if len(terr) > 4:
            terr = '9999'
        if len(tall) > 4:
            tall = '9999'

        h = self.H-1
        w = self.W-c2w-1
        self.win.addstr(h,w,tpass5.rjust(4),color)
        self.win.addstr(h,w+5,terr.rjust(4),color)
        self.win.addstr(h,w+10,tfail.rjust(4),color)
        self.win.addstr(h,w+15,tall.rjust(4),color)


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

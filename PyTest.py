#!/usr/bin/env python
"""This module defines three classes which provide the heavy lifting for the
pytest interpreter:

    1. Interpolator -- mixes testing framework into plain Python code
    2. Observer -- runs the interpolated code and monitors its execution
    3. utils -- convenience methods useful inside of a pytest script

For more information, see the pytest man page.
"""

__author__ = 'Chad Whitacre'
__version__ = '0.3'

import parser, symbol, sys, time, token, traceback
from StringIO import StringIO
from ASTutils import ASTutils

class PyTestException(Exception):
    pass

class Interpolator:
    """This class provides for interpolation of pytest framework into Python
    code.
    """

    def interpolate(self, block):
        """return the original block with our interpolations
        """
        self.cst = parser.suite(block).tolist(line_info=True)
        self.walk(self.cst)
        ast = parser.sequence2ast(self.cst)
        return ASTutils.ast2text(ast)

    def walk(self, cst):
        """walk an AST list (a cst?) and do our interpolation
        """
        i = 0
        for node in cst:
            i += 1
            if type(node) is type([]):
                # we have a list of subnodes; recurse
                self.walk(node)
            else:
                # we have an actual node; interpret it and act accordingly

                # if the node is a simple comparison, wrap it
                # TODO account for multiple small_stmts
                if (node in (symbol.stmt, symbol.suite)) and (i == 1):
                    # the i flag is to guard against the rare case where the
                    # node constant would be stmt or suite, and the line number
                    # would too

                    if cst[1][0] == symbol.simple_stmt:

                        # convert the cst stmt fragment to an AST
                        ast = parser.sequence2ast(self._stmt2file_input(cst))

                        if self._is_test(ast):
                            cst[1] = self._wrap(cst, COMPARING=True)[1]
                        elif ASTutils.hasnode(ast, symbol.print_stmt):
                            cst[1] = self._wrap(cst, PRINTING=True)[1]

    def _is_test(self, ast):
        """Given an AST, return a boolean
        """
        # a test is a comparison with more than one term
        if ASTutils.hasnode(ast, symbol.comparison):
            if ASTutils.hasnode(ast, symbol.comp_op):
                return True
        return False

    def _line_number(self, cst):
        """given a single stmt cst w/ line numbers, return the first line
        number in it
        """
        for node in cst:
            if type(node) in (type(()), type([])):
                if len(node) == 3:
                    if type(node[2]) is type(0):
                        return node[2]
                return self._line_number(node)
        return -1 # default

    def _wrap(self, stmt, COMPARING=False, PRINTING=False):
        """given a single simple comparison statement as a cst, return that
        statement wrapped with our testing function, also as a cst
        """

        # convert statement to a first-class cst
        cst = self._stmt2file_input(stmt)

        # convert first-class cst to source code, wrap it, and back again to cst
        old_source = ASTutils.ast2text(parser.sequence2ast(cst))
        # TODO prolly should wrap this in a string to be safe instead of using
        # literal string delimiters
        tmp = """__pytest__.intercept("%s", %s, globals(), locals(),""" +\
                                   """COMPARING=%s,PRINTING=%s)"""
        new_source = tmp % (old_source, self._line_number(cst), COMPARING, PRINTING)
        cst = parser.suite(new_source).tolist()

        # and extract our statement from the first-class cst
        return cst[1]

    def _stmt2file_input(self, cst):
        """Given a stmt (list or tuple), promote it to a file_input.

        Usage:

            >>> import parser
            >>> from ASTutils import ASTutils
            >>> ast = parser.suite("print 'hello world'")
            >>> stmt = ASTutils.getnodes(ast, 'stmt')[0]
            >>> parser.sequence2ast(stmt)
            Traceback (most recent call last):
                ...
            ParserError: parse tree does not use a valid start symbol
            >>> stmt = Interpolator()._stmt2file_input(stmt)
            >>> parser.sequence2ast(stmt)
            <parser.st object at 0x817c0d0>

        """
        if type(cst) in (type(()), type([])):
            if cst[0] == symbol.stmt:
                if type(cst) is type(()):
                    return ( symbol.file_input
                           , cst
                           , (token.NEWLINE, '')
                           , (token.ENDMARKER,'')
                            )
                elif type(cst) is type([]):
                    return [ symbol.file_input
                           , cst
                           , [token.NEWLINE, '']
                           , [token.ENDMARKER,'']
                            ]
            else:
                raise PyTestException, "input is not a stmt"
        else:
            raise PyTestException, "cst to promote must be list or tuple"



class Observer(StringIO):
    """This class executes, monitors, and reports on the execution of a pytest.
    """

    passes = 0
    failures = 0
    exceptions = 0

    stopwatch = None

    def __init__(self, filename, *arg, **kw):
        self.filename = filename
        StringIO.__init__(self, *arg, **kw)



    ##
    # main callables
    ##

    def run(self, text, globals, locals):
        """run the interpolated test script
        """
        try:
            exec text in globals, locals
        except:
            print >> sys.__stdout__, text
            print
            traceback.print_exc(file=sys.__stdout__)

    def intercept(self, statement, linenumber, globals, locals,
                  COMPARING=False, PRINTING=False):
        """Given a statement, some context, and a couple optional flags, write
        to our report. Since we are called from inside of the test, sys.stdout
        is actually our parent. However, we leave sys.stderr alone, and any
        exceptions in fixture will raise as normal.
        """

        if COMPARING:
            try:
                if eval(statement, globals, locals):
                    self.passes += 1
                else:
                    self.print_h2('Failure', statement, linenumber)
                    ast = parser.expr(statement)
                    for term in ASTutils.getnodes(ast, 'expr'):
                        tast = parser.sequence2ast(self._expr2eval_input(term))
                        text = ASTutils.ast2text(tast)
                        evaled = str(eval(text, globals, locals))
                        if text <> evaled:
                            self.print_h3(text, evaled)
                    print
                    print
                    self.failures += 1
            except:
                self.print_h2('Exception', statement, linenumber)
                traceback.print_exc(file=self)
                print
                print
                self.exceptions += 1

        elif PRINTING:
            self.print_h2('Output', statement, linenumber)
            exec statement in globals, locals
            print
            print


    ##
    # stopwatch
    ##

    def start_timer(self):
        self.stopwatch = time.time()

    def stop_timer(self):
        self.stopwatch = time.time() - self.stopwatch



    ##
    # report generation
    ##

    def report(self):
        self.print_summary()
        print self.getvalue()
        self.print_summary()

    def print_summary(self):
        """output a header for the report
        """
        total = self.passes + self.failures + self.exceptions
        summary_data = {}
        summary_data['total']       = str(total).rjust(4)
        summary_data['passes']      = str(self.passes).rjust(4)
        summary_data['failures']    = str(self.failures).rjust(4)
        summary_data['exceptions']  = str(self.exceptions).rjust(4)
        summary_data['seconds']     = ('%.1f' % self.stopwatch).rjust(6)

        summary_list = [
            "        passes: %(passes)s    ",
            "      failures: %(failures)s    ",
            "    exceptions: %(exceptions)s    ",
            " ---------------------- ",
            "   total tests: %(total)s    ",
            "                        ",
            "  time elapsed: %(seconds)ss "
                        ]
        summary_list = [l % summary_data for l in summary_list]

        self.print_h1(self.filename)
        print '#%s#' % (' '*78,)
        for line in summary_list:
            print '# %s #' % self._center(line, 76)
        print '#%s#' % (' '*78,)
        print '#'*80
        print



    ##
    # formatting helpers
    ##

    def print_h1(self, h):
        if len(h) >= 73:
            h = h[:73] + '...'
        print "#"*80
        print "# %s #" % self._center(h, 76)
        print "#"*80

    def print_h2(self, stype, h, lnum):
        if len(h) >= 49:
            h = h[:49] + '...'

        print '+' + '-'*78 + '+'
        print '| %s  %s  LINE: %s |' % ( stype.upper().ljust(10)
                                         , self._center(h, 52)
                                         , str(lnum).rjust(4)
                                          )
        print '+' + '-'*78 + '+'
        print

    def print_h3(self, h, b):
        """given a heading and a body, output them
        """
        if len(h) >= 73:
            h = h[:73] + '...'

        print h
        print '-'*80
        print b
        print

    def _center(self, s, i):
        """given a string s and an int i, return a string i chars long with s
        centered
        """
        slen = len(s)
        rpadding = (i - slen) / 2
        lpadding = rpadding + ((i - slen) % 2)
        return ' '*rpadding + s + ' '*lpadding

    def _expr2eval_input(self, expr):
        """given an expr as a list, promote it to an eval_input
        """
        return [symbol.eval_input,[symbol.testlist,[symbol.test,
                [symbol.and_test,[symbol.not_test,[symbol.comparison,
                 expr]]]]],[token.NEWLINE, ''],[token.ENDMARKER, '']]



class utils:
    """convenience methods for use in pytests
    """

    def catchException(func, *arg, **kw):
        try:
            func(*arg, **kw)
        except:
            return sys.exc_info()[0]
    catchException = staticmethod(catchException)




if __name__ == '__main__':
    import doctest
    doctest.testmod()


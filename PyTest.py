#!/usr/bin/env python
"""This module defines three classes which provide the heavy lifting for the
pytest interpreter:

    1. Interpolator -- mixes testing framework into plain Python code
    2. Observer -- runs the interpolated code and monitors its execution
    3. utils -- convenience methods useful inside of a pytest script

For more information, see the pytest documentation.
"""

import linecache
import os
import parser
import symbol
import sys
import time
import token
import traceback
from os import linesep
from StringIO import StringIO

from ASTutils import ASTutils

class PyTestException(Exception):
    pass

class Interpolator:
    """This class provides for interpolation of pytest framework into Python
    code.
    """

    def interpolate(self, block):
        """Given a block of code, return the same code + our testing framework.

        Our testing framework consists of calls to the Observer.intercept method
        wrapped around all tests and print statements. Tests are any explicit
        comparison statement, i.e., those with a comparison operator. The
        Observer.run method adds the Observer instance to the test script's
        namespace as __pytest__.

        Example:

            >>> block = "1 + 1 == 2"
            >>> Interpolator.interpolate(block)
            '__pytest__ . intercept ( "1 + 1 == 2" , 1 , globals ( ) , locals ( ) , COMPARING = True , PRINTING = False )'

            >>> block = "print 'hello world'"
            >>> Interpolator.interpolate(block)
            '__pytest__ . intercept ( "print \\\\\\'hello world\\\\\\'" , 1 , globals ( ) , locals ( ) , COMPARING = False , PRINTING = True )'


        """
        self.cst = parser.suite(block).tolist(line_info=True)
        self._walk(self.cst)
        ast = parser.sequence2ast(self.cst)
        return ASTutils.ast2text(ast)
    interpolate = classmethod(interpolate)

    def _walk(self, cst):
        """walk an AST list (a cst?) and do our interpolation
        """
        i = 0
        for node in cst:
            i += 1
            if type(node) is type([]):
                # we have a list of subnodes; recurse
                self._walk(node)
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
    _walk = classmethod(_walk)

    def _is_test(self, ast):
        """Given an AST, return a boolean
        """
        # a test is a comparison with more than one term
        if ASTutils.hasnode(ast, symbol.comparison):
            if ASTutils.hasnode(ast, symbol.comp_op):
                return True
        return False
    _is_test = classmethod(_is_test)

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
    _line_number = classmethod(_line_number)

    def _escape_source(self, s):
        """Given a string, make it safe to be strunged itself

            >>> import PyTest
            >>> i = PyTest.Interpolator()
            >>> print i._escape_source('foo')
            foo
            >>> print i._escape_source('"foo"')
            \\"foo\\"
            >>> print i._escape_source("'bar'")
            \\'bar\\'

        """
        s = s.replace("'", "\\'")
        s = s.replace('"', '\\"')
        return s
    _escape_source = classmethod(_escape_source)

    def _wrap(self, stmt, COMPARING=False, PRINTING=False):
        """given a single simple comparison statement as a cst, return that
        statement wrapped with our testing function, also as a cst
        """

        # convert statement to source code
        cst = self._stmt2file_input(stmt)
        old_source = ASTutils.ast2text(parser.sequence2ast(cst))
        old_source = self._escape_source(old_source)

        # escape string delimiters in old source code; convert to single line

        template = """\
__pytest__.intercept("%s", %s, globals(), locals(), COMPARING=%s,PRINTING=%s)"""
        new_source = template % ( old_source
                                , self._line_number(cst)
                                , COMPARING
                                , PRINTING
                                 )

        # convert back to a cst, extract our statement, and return
        cst = parser.suite(new_source).tolist()
        return cst[1]
    _wrap = classmethod(_wrap)

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
            >>> foo = parser.sequence2ast(stmt)
            >>> bar = parser.suite('')
            >>> type(foo) is type(bar)
            True

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
    _stmt2file_input = classmethod(_stmt2file_input)


class Observer(StringIO):
    """This class executes, monitors, and reports on the execution of a pytest.
    """

    passes = 0
    failures = 0
    exceptions = 0

    nontest_excs = 0

    stopwatch = None


    ##
    # main callables
    ##

    def run(self, filename, interpolated, globals, locals):
        """run the interpolated test script; if that fails, run the original
        script so that the traceback is accurate
        """

        # save this for a default header for our report
        self.filename = filename

        try:
            exec interpolated in globals, locals
        except:
            try:
                execfile(filename, globals, locals)
            except:
                linenumber = sys.exc_info()[2].tb_next.tb_lineno
                statement = linecache.getline(filename, linenumber)
                statement = statement.strip().split("#")[0]

                self.print_h2('Crisis', statement, linenumber)
                traceback.print_exc(file=self)
                print
                self.print_h2('', 'TEST TERMINATED', -1)
                print
                self.nontest_excs += 1

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
            self.print_h2('More Info', statement, linenumber)
            try:
                exec statement in globals, locals
            except:
                traceback.print_exc(file=self)
                self.nontest_excs += 1
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

    def report(self, heading=''):

        if not heading:
            heading = self.filename # this assumes we've been run

        self.print_summary(heading)
        print self.getvalue()
        self.print_summary(heading)

    def print_summary(self, heading):
        """output a header for the report
        """
        total = self.passes + self.failures + self.exceptions
        summary_data = {}
        summary_data['total']       = str(total).rjust(4)
        summary_data['passes']      = str(self.passes).rjust(4)
        summary_data['failures']    = str(self.failures).rjust(4)
        summary_data['exceptions']  = str(self.exceptions).rjust(4)
        summary_data['nontest_excs']  = str(self.nontest_excs).rjust(4)
        summary_data['seconds']     = ('%.1f' % self.stopwatch).rjust(6)

        summary_list = [
            "           passes: %(passes)s    ",
            "         failures: %(failures)s    ",
            "       exceptions: %(exceptions)s    ",
            "    ---------------------- ",
            "      total tests: %(total)s    ",
            "                           ",
            " other exceptions: %(nontest_excs)s    ",
            "                           ",
            "     time elapsed: %(seconds)ss "


                        ]
        summary_list = [l % summary_data for l in summary_list]

        self.print_h1(heading)
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

        if lnum <> -1:
            linenumber = "LINE: %s" % str(lnum).rjust(4)
        else:
            linenumber = "          "

        print '+' + '-'*78 + '+'
        print '| %s  %s  %s |' % ( stype.upper().ljust(10)
                                 , self._center(h, 52)
                                 , linenumber
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

    def catch_exc(func, *arg, **kw):
        try:
            func(*arg, **kw)
        except:
            return sys.exc_info()[0]
    catch_exc = staticmethod(catch_exc)




if __name__ == '__main__':
    import doctest
    doctest.testmod()


#!/usr/bin/env python
"""Pytest is an alternate python interpreter that interpolates its input with
testing framework before handing it off to the standard python interpreter.

A testing framework is composed of three things:

    1. fixture

    2. test

    3. reporting

The pytest philosophy is to use the python language *as it stands* to supply the
first two. Pytest treats python statements in the following way:

    1. All stand-alone, explicit comparison statements are considered tests.
       Tests which evaluate to True are tallied as 'passed'; False tests are
       tallied as 'failed' and a failure report is outputed on the report.
       Exceptions within tests are tallied as exceptions, and the traceback is
       outputed in the report.

    2. All print statements and pprint calls are channeled to the test report.
       Exceptions raised here are not caught.

    3. All other statements are considered fixture and are executed unaltered.

"""
# save for clean context for tested program
__globals__ = globals()
__locals__  = locals()

import parser, symbol, sys, token, traceback
from StringIO import StringIO
from ASTutils import ASTutils

class PyTestException(Exception):
    pass

class interpolator:
    """ given a block of python text, interpolate our framework into it
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
                        ast = parser.sequence2ast(ASTutils._stmt2file_input(cst))

                        if self._is_test(ast):
                            cst[1] = self._wrap(cst, COMPARING=True)[1]
                        elif ASTutils.hasnode(ast, symbol.print_stmt):
                            cst[1] = self._wrap(cst, PRINTING=True)[1]

    def _is_test(self, ast):
        """Given an AST, return a booleanq
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
        cst = ASTutils._stmt2file_input(stmt)

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
            >>> stmt = ASTutils.getnode(ast, 'stmt')
            >>> parser.sequence2ast(stmt)
            Traceback (most recent call last):
                ...
            ParserError: parse tree does not use a valid start symbol
            >>> stmt = _stmt2file_input(stmt)
            >>> parser.sequence2ast(stmt)
            <parser.st object at 0x817c090>

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



class observer(StringIO):

    passed = 0
    failed = 0
    exceptions = 0

    def __init__(self, filename, *arg, **kw):
        self.filename = filename
        StringIO.__init__(self, *arg, **kw)

    ##
    # main intercept wrapper
    ##

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
                    self.passed += 1
                else:
                    # GET MORE INFO
                    # resolve into components
                    # promote each comparison to its own AST
                    # evaluate each component and assign result to a variable
                    # loop over each

                    ast = parser.eval(statement)
                    results = []
                    for term in ASTutils.getnodes(ast, 'expr'):
                        term = self._expr2eval_input(term)
                        self.print_h3(term, eval(term, globals, locals))
                    self.print_h2('Failure', statement, linenumber)
                    print
                    print
                    self.failed += 1
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

    self._expr2eval_input(self, expr):
        """given an expr as a list, promote it to an eval_input
        """
        return [symbol.eval_input,[symbol.testlist,[symbol.test,
                [symbol.and_test,[symbol.not_test,[symbol.comparison,
                 [expr]]]]]],['NEWLINE', ''],['ENDMARKER', '']]

    ##
    # report generation
    ##

    def report(self):
        self.print_header()
        print self.getvalue()
        self.print_footer()

    def print_header(self):
        """output a header for the report
        """
        self.print_h1(self.filename)

    def print_footer(self):
        """output a footer for the report
        """

        total = self.passed + self.failed + self.exceptions
        #if self.failed + self.exceptions: print '\n'

        print """\
#######################
#       RESULTS       #
#######################
#                     #
#       passed: %s  #
#       failed: %s  #
#   exceptions: %s  #
# ------------------- #
#  total tests: %s  #
#                     #
#######################
""" % ( str(self.passed).rjust(4)
      , str(self.failed).rjust(4)
      , str(self.exceptions).rjust(4)
      , str(total).rjust(4))

    ##
    # formatting helpers
    ##

    def print_h1(self, s):
        print "#"*80
        print "# %s #" % self._center(s, 76)
        print "#"*80
        print

    def print_h2(self, stype, s, lnum):
        if len(s) >= 49:
            s = s[:49] + '...'

        print '+' + '-'*78 + '+'
        print '| %s  %s  LINE: %s |' % ( stype.upper().ljust(10)
                                         , self._center(s, 52)
                                         , str(lnum).rjust(4)
                                          )
        print '+' + '-'*78 + '+'
        print

    def _center(self, s, i):
        """given a string s and an int i, return a string i chars long with s
        centered
        """
        slen = len(s)
        rpadding = (i - slen) / 2
        lpadding = rpadding + ((i - slen) % 2)
        return ' '*rpadding + s + ' '*lpadding




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

    # interpret the arg on the command line as a filename to check

    arg = sys.argv[1:2]
    if not arg:
        print "usage: $ pytest [-arh] [filename]"
        raise SystemExit
    else:
        filename = arg[0]

    original = file(filename).read()
    interpolated = interpolator().interpolate(original)

    heisenberg = observer(filename)

    __globals__['__pytest__'] = sys.stdout = heisenberg
    exec interpolated in __globals__, __locals__
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    print heisenberg.report()

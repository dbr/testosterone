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

class interpolator:
    """ given a block of python text, interpolate our framework into it
    """

    def interpolate(self, block):
        """return the original block with our interpolations
        """
        self.cst = parser.suite(block).tolist()
        self.walk(self.cst)
        ast = parser.sequence2ast(self.cst)
        return ASTutils.ast2text(ast)

    def walk(self, cst):
        """walk an AST list (a cst?) and do our interpolation
        """
        for node in cst:
            if type(node) is type([]):
                # we have a list of subnodes; recurse
                self.walk(node)
            else:
                # we have an actual node; interpret it and act accordingly

                # convert the node to something human-readable
                readable_node = self._readable_node(node)

                # if the node is a simple comparison, wrap it
                # TODO account for multiple small_stmts
                if readable_node == 'stmt':
                    if cst[1][0] == symbol.simple_stmt:

                        # convert the cst stmt fragment to an AST
                        ast = parser.sequence2ast(ASTutils.promote_stmt(cst))

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

    def _readable_node(self, node):
        """given a single node (string or int), return a human-readable
        representation
        """
        if type(node) is type(0):
            if node < 256:
                readable_node = token.tok_name[node]
            else:
                readable_node = symbol.sym_name[node]
        else:
            readable_node = node
        return readable_node

    def _wrap(self, stmt, COMPARING=False, PRINTING=False):
        """given a single simple comparison statement as a cst, return that
        statement wrapped with our testing function, also as a cst
        """

        # convert statement to a first-class cst
        cst = [symbol.file_input,stmt,[token.NEWLINE, ''],[token.ENDMARKER,'']]

        # convert first-class cst to source code, wrap it, and back again to cst
        old_source = ASTutils.ast2text(parser.sequence2ast(cst))
        # TODO prolly should wrap this in a string to be safe instead of using
        # literal string delimiters
        tmp = """__pytest__.intercept("%s", globals(), locals(),""" +\
                                   """COMPARING=%s,PRINTING=%s)"""
        new_source = tmp % (old_source, COMPARING, PRINTING)
        cst = parser.suite(new_source).tolist()

        # and extract our statement from the first-class cst
        return cst[1]


class observer(StringIO):

    passed = 0
    failed = 0
    exceptions = 0

    ##
    # main intercept wrapper
    ##

    def intercept(self, statement, globals, locals,
                  COMPARING=False, PRINTING=False):
        """Given a statement, some context, and a couple optional flags, write
        to our report. Since we are called from inside of the test, sys.stdout
        is actually our parent. :^)
        """

        if COMPARING:
            try:
                if eval(statement, globals, locals):
                    self.passed += 1
                else:
                    print 'False: %s' % statement
                    print
                    self.failed += 1
            except:
                print statement
                print '-'*79
                traceback.print_exc(file=self) # not sure why we need file=self
                print
                self.exceptions += 1

        elif PRINTING:
            print statement
            print '-'*79
            exec statement in globals, locals
            print

    ##
    # report generation
    ##

    #def write(self, s):
    #    """overriding StringIO's write method to provide extra formatting
    #    """
    #
    #    from os import linesep
    #
    #    if s == linesep:
    #        s = linesep + '-'*79
    #    else:
    #        s = linesep + '| ' + s[:-2]
    #    StringIO.write(self, s)


    def report(self):
        self.print_header()
        print self.getvalue()
        self.print_footer()

    def print_header(self):
        """output a header for the report
        """
        print
        print "#"*79
        print "#"+"running tests ...".rjust(47)+" "*30+"#"
        print "#"*79
        print

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
        arg = arg[0]

    original = file(arg).read()
    interpolated = interpolator().interpolate(original)

    heisenberg = observer()

    __globals__['__pytest__'] = sys.stdout = heisenberg
    exec interpolated in __globals__, __locals__
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    print heisenberg.report()

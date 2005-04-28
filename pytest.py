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


import parser, symbol, sys, token
from astutils import ast2read, ast2text

class interpolator:
    """ given a block of python text, interpolate our framework into it
    """

    def interpolate(self, block):
        """return the original block with our interpolations
        """
        self.cst = parser.suite(block).tolist()
        self.walk(self.cst)
        ast = parser.sequence2ast(self.cst)
        return ast2text(ast)

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
                        if self._is_comparison(cst):
                            cst[1] = self._wrap(cst)[1]

    def _readable_node(self, node):
        """given a single node, return a human-readable representation
        """
        if type(node) is type(0):
            if node < 256:
                readable_node = token.tok_name[node]
            else:
                readable_node = symbol.sym_name[node]
        else:
            readable_node = node
        return readable_node

    def _is_comparison(self, node):
        """ given a node, return a boolean
        """
        for subnode in node:
            if type(subnode) is type([]):
                return self._is_comparison(subnode)
            else:
                if subnode == symbol.comparison:
                    return True
        return False

    def _wrap(self, stmt):
        """given a single simple comparison statement as a cst, return that
        statement wrapped with our testing function, also as a cst
        """

        # convert statement to a first-class cst
        cst = [symbol.file_input,stmt,[token.NEWLINE, ''],[token.ENDMARKER,'']]

        # convert first-class cst to source code, wrap it, and back again to cst
        old_source = ast2text(parser.sequence2ast(cst))
        # TODO prolly should wrap this in a string to be safe instead of using
        # literal string delimiters
        new_source = "__pytest__.intercept('%s', globals(), locals())" % old_source
        cst = parser.suite(new_source).tolist()

        # and extract our statement from the first-class cst
        return cst[1]


class reporter:

    passed = 0
    failed = 0
    exceptions = 0

    def intercept(self, statement, globals, locals,
                  COMPARING=False, PRINTING=False):
        """given a statement, some context, and a couple optional flags,
        """
        if COMPARING:
            try:
                if eval(statement, globals, locals):
                    self.passed += 1
                else:
                    self.failed += 1
            except:
                self.exceptions += 1

        elif PRINTING:
            print >> self.out, '\n'
            print >> self.out, statement
            print >> self.out, '-'*79
            exec statement in globals, locals
            print >> self.out, '\n'

        else:
            exec statement in globals, locals


if __name__ == '__main__':

    # interpret the arg on the command line as a

    arg = sys.argv[1:2]
    if not arg:
        print "usage: $ pytest [-arh] [filename]"
        raise SystemExit
    else:
        arg = arg[0]

    original = file(arg).read()
    interpolated = interpolator().interpolate(original)

    heisenberg = reporter()
    __globals__['__pytest__'] = heisenberg
    exec interpolated in __globals__, __locals__

    print heisenberg.passed

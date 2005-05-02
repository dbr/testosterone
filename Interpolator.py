#!/usr/bin/env python
"""This module defines the Interpolator class.
"""

import parser
import symbol
import token

from pytest import PyTestException
from pytest.ASTutils import ASTutils

class Interpolator:
    """This class interpolates pytest framework into Python code.
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


if __name__ == '__main__':
    import doctest
    doctest.testmod()

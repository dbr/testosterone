#!/usr/bin/env python
"""utilities for working with syntax tree (AST) objects
"""
# (c) 2005 Chad Whitacre <http://www.zetadev.com/>
# This program is beerware. If you like it, buy me a beer someday.
# No warranty is expressed or implied.

__version__ = '0.2.0'
__author__ = 'Chad Whitacre'
__author_email__ = 'chad [at] zetaweb [dot] com'
__url__ = 'http://www.zetadev.com/'

import parser, token, symbol
from os import linesep
from pprint import pformat
from StringIO import StringIO

class ASTutilsException(Exception):
    """This represents an error in one of the ASTutils methods.
    """

class ASTutils:
    """This class holds four utilities for working with Python syntax trees.

    Syntax trees are the output of the Python parser, which is mimicked in the
    standard library's parser module. The parser module trades in AST objects,
    which represent "abstract syntax trees." The parser module can convert ASTs
    to list and tuple representations. I believe that these are considered
    "concrete syntax trees," or CSTs. The compiler module also works with ASTs,
    but I believe at a higher level. This module uses parser, but not compiler.

    Where an 'st' argument is called for in this module, you may provide either
    an AST object, or a list or tuple as produced by parser.ast2list and
    parser.ast2tuple. This module uses the term "cst fragment" to refer to a
    fragment of a syntax tree sequence that does not represent a well-formed
    Python structure, e.g., the tree does not begin with one of: single_input,
    file_input, or eval_input. Unless otherwise mentioned, syntax trees provided
    as 'st' arguments must be well-formed; they may not be fragments.

    For the record, I implemented these as classmethods rather than as
    module-level functions because they call each other and I didn't want to
    think about the order they were defined in.

    """


    def _standardize_st(self, st, format='tuple'):
        """Given a syntax tree and a desired format, return the tree in that
        format.
        """
        # convert the incoming ast/cst into an AST
        if type(st) is type(parser.suite('')):
            ast = st
        else:
            if type(st) in (type(()), type([])):
                ast = parser.sequence2ast(st)
            else:
                raise ASTutilsException, "incoming type unrecognized: " +\
                                         repr(type(st))

        # return the tree in the desired format
        formats = { 'tuple' : ast.totuple
                  , 'list'  : ast.tolist
                  , 'ast'   : lambda: ast
                   }

        outgoing = formats.get(format.lower())
        if outgoing is None:
            raise ASTutilsException, "requested format unrecognized: " + format

        return outgoing()

    _standardize_st = classmethod(_standardize_st)



    def ast2read(self, st):
        """Given a syntax tree, return a more human-readable representation of
        the tree than is returned by parser.ast2list and parser.ast2tuple.

        Usage:

        >>> import parser
        >>> ast = parser.suite("print 'hello world'")
        >>> print parser.ast2list(ast)
        [257, [266, [267, [268, [271, [1, 'print'], [298, [299, [300, [301, [303, [304, [305, [306, [307, [308, [309, [310, [311, [3, "'hello world'"]]]]]]]]]]]]]]]], [4, '']]], [0, '']]
        >>> print ASTutils.ast2read(ast)
        ['file_input',
         ['stmt',
          ['simple_stmt',
           ['small_stmt',
            ['print_stmt',
             ['NAME', 'print'],
             ['test',
              ['and_test',
               ['not_test',
                ['comparison',
                 ['expr',
                  ['xor_expr',
                   ['and_expr',
                    ['shift_expr',
                     ['arith_expr',
                      ['term',
                       ['factor',
                        ['power',
                         ['atom', ['STRING', "'hello world'"]]]]]]]]]]]]]]]],
           ['NEWLINE', '']]],
         ['ENDMARKER', '']]
        """

        # define our recursive function
        def walk(cst):
            """Given an AST list, recursively walk it and replace the nodes with
            human-readable equivalents.
            """

            for node in cst:
                if type(node) is type([]):
                    # we have a list of subnodes; recurse
                    walk(node)
                else:
                    # we have an actual node; interpret it and store the result
                    if type(node) is type(0):
                       if node < 256:
                            readable_node = token.tok_name[node]
                       else:
                            readable_node = symbol.sym_name[node]
                    else:
                        readable_node = node

                    cst[cst.index(node)] = readable_node

        # ggg!
        TREE = self._standardize_st(st, 'list')
        walk(TREE)
        return pformat(TREE)

    ast2read = classmethod(ast2read)



    def ast2text(self, st):
        """Given a syntax tree, return an approximation of the source code that
        generated it. The approximation will only differ from the original in
        non-essential whitespace and missing comments.

        Usage:

            >>> import parser
            >>> from ASTutils import ASTutils
            >>> ast = parser.suite("print 'hello world'")
            >>> print ASTutils.ast2text(ast)
            print 'hello world'

            >>> # Here's an example of whitespace differences (this also tests
            >>> # multiple indent levels):
            >>>
            >>> from os import linesep as lf
            >>> block = "def foo():"+lf+" if 1:"+lf+"  return True"
            >>> # note no whitespace around parens/colons and one-space indents
            >>>
            >>> ast = parser.suite(block)
            >>> text = ASTutils.ast2text(ast)
            >>>
            >>> # account for the fact that I trim trailing spaces in my editor
            >>> text = linesep.join([l.rstrip() for l in text.split(linesep)])
            >>> print text
            def foo ( ) :
                if 1 :
                    return True
            >>> # note extra spacing around parens/colons and four-space indents

        """

        class walker:

            TEXT = ''
            INDENT_LEVEL = 0

            def walk(self, cst):
                """Given an AST tuple (a CST?), recursively walk it and
                assemble the nodes back into a text code block.
                """

                for node in cst:
                    if type(node) is type(()):
                        # we have a tuple of subnodes; recurse
                        self.walk(node)
                    else:
                        # we have an actual node; interpret it and store the
                        # result

                        text = '' # default

                        if type(node) is type(''):
                            if node <> '':
                                node += ' ' # insert some whitespace
                            if not node.startswith('#'):
                                text = node # ignore comments

                        elif node == token.NEWLINE:
                            text = linesep + self.indent()

                        elif node == token.INDENT:
                            self.INDENT_LEVEL += 1
                            text = '    '

                        elif node == token.DEDENT:
                            self.INDENT_LEVEL -= 1
                            self.dedent()

                        self.TEXT += text
            walk = classmethod(walk)

            def indent(self):
                if self.INDENT_LEVEL == 0:
                    return ''
                else:
                    return self.INDENT_LEVEL * '    '
            indent = classmethod(indent)

            def dedent(self):
                self.TEXT = self.TEXT[:-4]
            dedent = classmethod(dedent)

        cst = self._standardize_st(st, 'tuple')
        walker.walk(cst)

        # trim a possible trailing newline and/or space; this is necessary to
        # make the doctest work

        output = walker.TEXT
        if output.endswith(linesep): output = output.rstrip(linesep)
        if output.endswith(' '):  output = output[:-1]

        return output

    ast2text = classmethod(ast2text)



    def getnodes(self, st, nodetype):
        """Given an AST object or a cst fragment (as list or tuple), and a
        string or int nodetype, return the first instance of the desired
        nodetype as a cst fragment, or None if the nodetype is not found.

        Usage:

            >>> import parser, symbol
            >>> ast = parser.suite("print 'hello world'")
            >>> ASTutils.getnodes(ast, 'print_stmt')
            [(271, (1, 'print'), (298, (299, (300, (301, (303, (304, (305, (306, (307, (308, (309, (310, (311, (3, "'hello world'")))))))))))))))]
            >>> ASTutils.getnodes(ast, symbol.pass_stmt)
            []
            >>> ASTutils.getnodes(ast, -1) # bad data
            Traceback (most recent call last):
                ...
            ASTutilsException: nodetype '-1' is not in symbol or token tables
            >>> ASTutils.getnodes(ast, 'foo') # bad data
            Traceback (most recent call last):
                ...
            ASTutilsException: nodetype '-1' is not in symbol or token tables

        """

        # we don't call _standardize_st because we want to accept fragments
        ast = parser.suite('')
        if type(st) is type(ast):
            cst = st.totuple()
        else:
            cst = st

        # standardize the incoming nodetype to a symbol or token int
        if type(nodetype) is type(''):
            symtype = getattr(symbol, nodetype, '')
            if symtype:
                nodetype = symtype
            else:
                toktype = getattr(token, nodetype, '')
                if toktype:
                    nodetype = toktype
                else:
                    nodetype = -1 # bad data

        # validate the input
        valid_ints = symbol.sym_name.keys() + token.tok_name.keys()
        if nodetype not in valid_ints:
            raise ASTutilsException, "nodetype '%s' " % nodetype +\
                                     "is not in symbol or token tables"

        # define our recursive function
        class walker:

            NODES = []

            def walk(self, cst, nodetype):
                for node in cst:
                    if type(node) in (type(()), type([])):
                        candidate = self.walk(node, nodetype)
                    else:
                        candidate = cst
                    if candidate is not None:
                        if candidate[0] == nodetype:
                            self.NODES.append(candidate)
            walk = classmethod(walk)

        # ggg!
        walker.walk(cst, nodetype)
        return walker.NODES

    getnodes = classmethod(getnodes)



    def hasnode(self, cst, nodetype):
        """Given an AST object or a cst fragment (either in list or tuple form),
        and a nodetype (either as a string or an int), return a boolean.

        Usage:

            >>> import parser, symbol
            >>> ast = parser.suite("print 'hello world'")
            >>> ASTutils.hasnode(ast, 'print_stmt')
            True
            >>> ast = parser.suite("if 1: print 'hello world'")
            >>> ASTutils.hasnode(ast, symbol.pass_stmt)
            False
            >>> ASTutils.hasnode(ast, symbol.print_stmt)
            True

        """
        return len(self.getnodes(cst, nodetype)) > 0

    hasnode = classmethod(hasnode)



if __name__ == "__main__":
    import doctest
    doctest.testmod()

import sys
import unittest

from testosterone.cli.reporters import detail, _Summarize
from testosterone.tests.utils import reportersTestCase


OUTPUT_START="""\
-------------------------------<| testosterone |>-------------------------------
.EF..
======================================================================
ERROR: test_errs (testostertests.TestCase)
----------------------------------------------------------------------
Traceback (most recent call last):"""; """
<snip>
StandardError: heck

======================================================================
FAIL: test_fails (testostertests.TestCase)
----------------------------------------------------------------------
Traceback (most recent call last):
<snip>
AssertionError

----------------------------------------------------------------------
Ran 5 tests in 0.002s"""; OUTPUT_END="""

FAILED (failures=1, errors=1)
"""


REPORT_SUCCESS = """\
-------------------------------<| testosterone |>-------------------------------
..
----------------------------------------------------------------------
Ran 2 tests in 0.000s

OK
"""



class Detail(reportersTestCase):

    def testOnlyModuleNoTestCaseTriggersNameError(self):
        self.assertRaises(TypeError, detail, 'needsADot')

    def testBadModuleTriggersImportError(self):
        self.assertRaises(ImportError, detail, 'probablyDoesntExist', 'TestCase')

    def testBadTestCaseNameAlsoTriggersImportError(self):
        self.assertRaises(ImportError, detail, 'testostertests', 'ToastCase')

    def testBadTestCaseTriggersTypeError(self):
        self.assertRaises(TypeError, detail, 'testostertests', 'itDoesExist')

    def testReturnsNormalUnitTestOutputWithOurBanner(self):
        actual = detail('testostertests', 'TestCase')
        start = actual[:len(OUTPUT_START)]
        end = actual[-len(OUTPUT_END):]
        self.assertEqual(start, OUTPUT_START)
        self.assertEqual(end, OUTPUT_END)

    def testDoesntContainProgramOutput(self):
        actual = detail('testostertests', 'TestCase')
        start = actual[:len(OUTPUT_START)]
        end = actual[-len(OUTPUT_END):]
        self.assertEqual(start, OUTPUT_START)
        self.assertEqual(end, OUTPUT_END)

    def testTestCaseInSubmodulesWorks(self):
        expected = REPORT_SUCCESS
        actual = detail('testostertests.itDoesExist', 'TestCase')
        self.assertEqual(expected, actual)




HEADER = """\
-------------------------------<| testosterone |>-------------------------------
MODULE                                                       PASS FAIL  ERR  ALL
--------------------------------------------------------------------------------
"""

BODY = """\
testostertests.TestCase                                       60%    1    1    5
testostertests.itDoesExist.TestCase                          100%    0    0    2
testostertests.itDoesExist.TestCase2                         100%    0    0    1
testostertests.subpkg.TestCase                               100%    0    0    2
"""
BODY_FIND = """\
testostertests.TestCase                                        -     -    -    5
testostertests.itDoesExist.TestCase                            -     -    -    2
testostertests.itDoesExist.TestCase2                           -     -    -    1
testostertests.subpkg.TestCase                                 -     -    -    2
"""
BODY_DOTTED_RUN_VERBOSE = """\
testostertests.itDoesExist.TestCase                          100%    0    0    2
testostertests.itDoesExist.TestCase2                         100%    0    0    1
"""


TOTALS_BASIC = """\
--------------------------------------------------------------------------------
TOTALS                                                        50%    4    5   18
"""
TOTALS_BASIC_NO_RUN = """\
--------------------------------------------------------------------------------
TOTALS                                                         -     -    -   18
"""
TOTALS_ZERO = """\
--------------------------------------------------------------------------------
TOTALS                                                         0%    0    0    0
"""
TOTALS_ZERO_NO_RUN = """\
--------------------------------------------------------------------------------
TOTALS                                                         -     -    -    0
"""
TOTALS_ZERO_PERCENT = """\
--------------------------------------------------------------------------------
TOTALS                                                         0%    5    5   10
"""
TOTALS_ZERO_PERCENT_NO_RUN = """\
--------------------------------------------------------------------------------
TOTALS                                                         -     -    -   10
"""
TOTALS_ALL_PASSING = """\
--------------------------------------------------------------------------------
TOTALS                                                       100%    0    0   10
"""
TOTALS_ALL_PASSING_NO_RUN = """\
--------------------------------------------------------------------------------
TOTALS                                                         -     -    -   10
"""
TOTALS_SUMMARIZE = """\
--------------------------------------------------------------------------------
TOTALS                                                        80%    1    1   10
"""

SUMMARIZE = HEADER + BODY + TOTALS_SUMMARIZE


class Summary(reportersTestCase):

    def setUpUp(self):
        self.summarize = _Summarize()
        self.summarize.module = 'testostertests'
        self.summarize.find_only = False
        self.summarize.stopwords = ()


    # __call__
    # ========

    def testSummarize(self):
        expected = SUMMARIZE
        actual = self.summarize('testostertests')
        self.assertEqual(expected, actual)

    def testTestCaseTriggersImportError(self):
        self.assertRaises(ImportError, self.summarize, 'testostertests.TestCase')


    # load_testcases
    # ==============

    def testLoadTestCases(self):
        mod = __import__('testostertests')
        expected = [('testostertests.TestCase', mod.TestCase)]
        actual = self.summarize.load_testcases(mod)
        self.assertEqual(expected, actual)

    def testLoadTestCasesDottedAndMultiple(self):
        mod = __import__('testostertests.itDoesExist')
        expected = [ ( 'testostertests.itDoesExist.TestCase'
                     , mod.itDoesExist.TestCase
                      )
                   , ( 'testostertests.itDoesExist.TestCase2'
                     , mod.itDoesExist.TestCase2
                      )
                    ]
        actual = self.summarize.load_testcases(mod.itDoesExist)
        self.assertEqual(expected, actual)

    def testLoadTestCasesOnlyIfTheyHaveTests(self):
        mod = __import__('testostertests.subpkg')
        reload(mod.subpkg)
        expected = [ ( 'testostertests.subpkg.TestCase'
                     , mod.subpkg.TestCase
                      )
                    ]
        actual = self.summarize.load_testcases(mod.subpkg)
        self.assertEqual(expected, actual)
        self.setUp()


    # find_testcases
    # ==============

    def testFindTestCases(self):
        self.summarize.module = 'testostertests'
        self.summarize.find_testcases()
        mod = __import__('testostertests')
        expected = [ ( 'testostertests.TestCase'
                     , mod.TestCase
                      )
                   , ( 'testostertests.itDoesExist.TestCase'
                     , mod.itDoesExist.TestCase
                      )
                   , ( 'testostertests.itDoesExist.TestCase2'
                     , mod.itDoesExist.TestCase2
                      )
                   , ( 'testostertests.subpkg.TestCase'
                     , mod.subpkg.TestCase
                      )
                    ]
        actual = self.summarize._Summarize__testcases
        self.assertEqual(expected, actual)

    def testFindTestCasesStopWords(self):
        self.summarize.module = 'testostertests'
        self.summarize.stopwords = ('Does',)
        self.summarize.find_testcases()
        mod = __import__('testostertests')
        expected = [ ('testostertests.TestCase', mod.TestCase)
                   , ('testostertests.subpkg.TestCase', mod.subpkg.TestCase)]
        actual = self.summarize._Summarize__testcases
        self.assertEqual(expected, actual)

    def testFindTestCasesEmptyStopWordsOk(self):
        self.summarize.module = 'testostertests'
        self.summarize.stopwords = ('',)
        self.summarize.find_testcases()
        mod = __import__('testostertests')
        expected = [ ( 'testostertests.TestCase'
                     , mod.TestCase
                      )
                   , ( 'testostertests.itDoesExist.TestCase'
                     , mod.itDoesExist.TestCase
                      )
                   , ( 'testostertests.itDoesExist.TestCase2'
                     , mod.itDoesExist.TestCase2
                      )
                   , ( 'testostertests.subpkg.TestCase'
                     , mod.subpkg.TestCase
                      )
                    ]
        actual = self.summarize._Summarize__testcases
        self.assertEqual(expected, actual)


    # print_header
    # ============

    def testPrintHeader(self):
        self.summarize.print_header()
        actual = self.summarize.report.getvalue()
        expected = HEADER
        self.assertEqual(expected, actual)


    # print_body
    # ==========

    def testPrintBody(self):
        self.summarize.module = 'testostertests'
        self.summarize.find_testcases()
        self.summarize.print_body()

        expected = BODY
        actual = self.summarize.report.getvalue()
        self.assertEqual(expected, actual)

        expected = (1, 1, 10)
        actual = self.summarize._Summarize__totals
        self.assertEqual(expected, actual)

    def testPrintBodyNoRun(self):
        self.summarize.module = 'testostertests'
        self.summarize.find_only = True
        self.summarize.find_testcases()
        self.summarize.print_body()

        expected = BODY_FIND
        actual = self.summarize.report.getvalue()
        self.assertEqual(expected, actual)

        expected = (0, 0, 10)
        actual = self.summarize._Summarize__totals
        self.assertEqual(expected, actual)

    def testPrintBodyBaseIsDotted(self):
        self.summarize.module = 'testostertests.itDoesExist'
        self.summarize.find_testcases()
        self.summarize.quiet = False
        self.summarize.print_body()

        expected = BODY_DOTTED_RUN_VERBOSE
        actual = self.summarize.report.getvalue()
        self.assertEqual(expected, actual)

        expected = (0, 0, 3)
        actual = self.summarize._Summarize__totals
        self.assertEqual(expected, actual)



    # print_footer
    # ============

    def testPrintFooterBasicTotalsWithRun(self):
        self.summarize._Summarize__totals = (4, 5, 18)
        self.summarize.print_footer()
        actual = self.summarize.report.getvalue()
        expected = TOTALS_BASIC
        self.assertEqual(expected, actual)

    def testPrintFooterBasicTotalsNoRun(self):
        self.summarize._Summarize__totals = (4, 5, 18)
        self.summarize.find_only = True
        self.summarize.print_footer()
        actual = self.summarize.report.getvalue()
        expected = TOTALS_BASIC_NO_RUN
        self.assertEqual(expected, actual)

    def testPrintFooterZeroTotalsWithRun(self):
        self.summarize._Summarize__totals = (0, 0, 0)
        self.summarize.print_footer()
        actual = self.summarize.report.getvalue()
        expected = TOTALS_ZERO
        self.assertEqual(expected, actual)

    def testPrintFooterZeroTotalsNoRun(self):
        self.summarize._Summarize__totals = (0, 0, 0)
        self.summarize.find_only = True
        self.summarize.print_footer()
        actual = self.summarize.report.getvalue()
        expected = TOTALS_ZERO_NO_RUN
        self.assertEqual(expected, actual)

    def testPrintFooterZeroPercentWithRun(self):
        self.summarize._Summarize__totals = (5, 5, 10)
        self.summarize.print_footer()
        actual = self.summarize.report.getvalue()
        expected = TOTALS_ZERO_PERCENT
        self.assertEqual(expected, actual)

    def testPrintFooterZeroPercentNoRun(self):
        self.summarize._Summarize__totals = (5, 5, 10)
        self.summarize.tfail = 5
        self.summarize.terr = 5
        self.summarize.tall = 10
        self.summarize.find_only = True
        self.summarize.print_footer()
        actual = self.summarize.report.getvalue()
        expected = TOTALS_ZERO_PERCENT_NO_RUN
        self.assertEqual(expected, actual)

    def testPrintFooterAllPassing(self):
        self.summarize._Summarize__totals = (0, 0, 10)
        self.summarize.tfail = 0
        self.summarize.terr = 0
        self.summarize.tall = 10
        self.summarize.print_footer()
        actual = self.summarize.report.getvalue()
        expected = TOTALS_ALL_PASSING
        self.assertEqual(expected, actual)

    def testPrintFooterAllPassingNoRun(self):
        self.summarize._Summarize__totals = (0, 0, 10)
        self.summarize.tfail = 0
        self.summarize.terr = 0
        self.summarize.tall = 10
        self.summarize.find_only = True
        self.summarize.print_footer()
        actual = self.summarize.report.getvalue()
        expected = TOTALS_ALL_PASSING_NO_RUN
        self.assertEqual(expected, actual)

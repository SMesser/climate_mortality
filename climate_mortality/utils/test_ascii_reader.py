'''Tests for files.py'''
from unittest import TestCase

from .ascii_reader import (
    ASCIIFormat,
    asc_to_array,
    asc_to_filtered_csv,
    read_token,
    skip_this_ndx,
    skip_this_pos
)


TEST_ASC = './test_cases/prec_1.asc'

class ASCIITest(TestCase):

    # Test functions with only external dependencies.
    
    def test_read_token(self):
        expected_first =             [
            'ncols',
            '100',
            'nrows',
            '101',
            'xllcorner',
            '-119.99999687076',
            'yllcorner',
            '-9.9999973922968',
            'cellsize',
            '0.0083333337679505',
            'NODATA_value',
            '-9999',
            '79',
            '81',
            '83'
        ]

        with open(TEST_ASC, 'r') as fp:
            for expectation in expected_first:
                self.assertEqual(read_token(fp), expectation)
        
    def test_skip_this_ndx(self):
        # Both conditions say skip.
        self.assertTrue(skip_this_ndx(1, 1, 57, 78))
        
        # trivial no-skip
        self.assertFalse(skip_this_ndx(0, 0, 84, 2123))

        # non-trivial no-skip
        self.assertFalse(skip_this_ndx(36, 77, 11, 10))

        # x skip
        self.assertTrue(skip_this_ndx(43, 4, 10, 3))

        # y skip
        self.assertTrue(skip_this_ndx(7, 8, 6, 6))

    def test_skip_this_pos(self):
        # defaults, no skip
        self.assertFalse(skip_this_pos(5, 6))
        # defaults, x skip
        self.assertTrue(skip_this_pos(-448, 9))
        # defaults, y skip
        self.assertTrue(skip_this_pos(-18, 190))        
        # defaults, double skip
        self.assertTrue(skip_this_pos(-189, 98))
        
        # y default, no skip
        self.assertFalse(skip_this_pos(15, 26, xmin=3, xmax=45))
        # y defaults x skip
        self.assertTrue(skip_this_pos(-48, -29, xmin=6, xmax=78))
        # y default, y skip
        self.assertTrue(skip_this_pos(-8, 96, xmin=-12, xmax=90))        
        # y default, double skip
        self.assertTrue(skip_this_pos(-18, -98, xmin=-45, xmax=-23))

        # x default, no skip
        self.assertFalse(skip_this_pos(15, 26, ymin=3, ymax=45))
        # x defaults x skip
        self.assertTrue(skip_this_pos(-248, -29, ymin=-78, ymax=-6))
        # x default, y skip
        self.assertTrue(skip_this_pos(-8, -26, ymin=-12, ymax=90))        
        # x default, double skip
        self.assertTrue(skip_this_pos(-183, -18, ymin=-45, ymax=-23))

        # no default, no skip
        self.assertFalse(skip_this_pos(45, 26, xmin=34, xmax=56, ymin=3, ymax=45))
        # no defaults x skip
        self.assertTrue(skip_this_pos(-48, -29, xmin=34, xmax=56, ymin=-78, ymax=-6))
        # no default, y skip
        self.assertTrue(skip_this_pos(48, -26, xmin=34, xmax=56, ymin=-12, ymax=90))        
        # no default, double skip
        self.assertTrue(skip_this_pos(-3, -18, xmin=34, xmax=56, ymin=-45, ymax=-23))

    # Test functions with internal dependencies.

    def test_asc_to_array(self):
        arr = asc_to_array(TEST_ASC)
        self.assertTrue(len(arr) <= 100 * 101)
        
        # The smaller the values of xskip & yskip, the longer the test runs.s
        xskip = 3
        yskip = 3
        arr = asc_to_array(TEST_ASC, xskip=xskip, yskip=yskip)
        self.assertTrue(len(arr) > 0)  # Confirm we read _something_
        self.assertTrue(  # Confirm we didn't read more than max expected
            len(arr) <= (100 * 101 / ((xskip+1) * (yskip+1)))
        )
        # Check first elementin detail
        self.assertEqual(len(arr[0]), 3)
        self.assertAlmostEqual(arr[0][0], -119.99999687076, 4)
        self.assertAlmostEqual(arr[0][2], 79.0, 4)
        
        with open(TEST_ASC, 'r') as fp:
            fmt = ASCIIFormat(fp)

        longitude = [loc[0] for loc in arr]
        self.assertGreaterEqual(min(longitude), fmt.xllcorner)
        latitude = [loc[1] for loc in arr]
        self.assertGreaterEqual(min(latitude), fmt.yllcorner)
        
    # Test classes.

    def test_init_ASCIIFormat(self):
        with open(TEST_ASC, 'r') as fp:
            fmt = ASCIIFormat(fp)

        self.assertEqual(fmt.ncols, 100)
        self.assertEqual(fmt.nrows, 101)
        self.assertAlmostEqual(fmt.xllcorner, -120.0, 3)
        self.assertAlmostEqual(fmt.yllcorner, -10.0, 3)
        self.assertAlmostEqual(fmt.cellsize, 0.008333, 6)
        self.assertEqual(fmt.null, '-9999')
                          

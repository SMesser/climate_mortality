'''Tests for noaa_reader.py.

 ~/Documents/UMUC/DATA 670/code (master)
$ python -m unittest utils.test_noaa_reader

'''
from unittest import TestCase

from .noaa_reader import (
    DATA_COLUMNS,
    ID_COLUMNS,
    read_source_header
)


class NOAATest(TestCase):

    # Test functions with only external dependencies.
    
    def test_read_source_header__defaults(self):
        expectation = DATA_COLUMNS

        with open('./test_cases/AG000060680.csv') as fp:
            source, filtered_data_fields = read_source_header(
                fp,
                id_fields=ID_COLUMNS,
                data_fields=DATA_COLUMNS
            )
            self.assertEqual(set(filtered_data_fields), expectation)

    def test_read_source_header__missing_id(self):
        with open('./test_cases/AG000060680.csv') as fp:
            with self.assertRaises(ValueError):
                read_source_header(
                    fp,
                    id_fields=ID_COLUMNS | {'BLUE'},
                    data_fields=DATA_COLUMNS
                )
                          
    def test_read_source_header__fewer_data(self):
        expectation = {'EMNT', 'PRCP', 'TMIN', 'TMAX'}

        with open('./test_cases/AG000060680.csv') as fp:
            source, filtered_data_fields = read_source_header(
                fp,
                id_fields=ID_COLUMNS,
                data_fields=expectation
            )
            self.assertEqual(set(filtered_data_fields), expectation)

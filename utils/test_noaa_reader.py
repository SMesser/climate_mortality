'''Tests for noaa_reader.py.

 ~/Documents/UMUC/DATA 670/code (master)
$ python -m unittest utils.test_noaa_reader

'''
from random import randint
from unittest import TestCase

from .noaa_reader import (
    DATA_COLUMNS,
    ID_COLUMNS,
    read_source_header,
    _print_group_update,
    _to_be_written
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

    def test__print_group_update(self):
        '''Just check that the print statement doesn't crash...'''
        full_in_files = randint(1, 100000)
        used_in_files = randint(0, 100000)
        in_records = randint(0, 5000000)
        _print_group_update(full_in_files, used_in_files, in_records)

    def test__to_be_written(self):
        # True
        self.assertTrue(
            _to_be_written('ao', {'ao': '5', 'DATE': 'today'}, 'today')
        )

        # False - missing key
        self.assertFalse(
            _to_be_written('aka', {'ao': '5', 'DATE': 'today'}, 'today')
        )

        # False - missing value
        self.assertFalse(
            _to_be_written('aka', {'aka': '', 'DATE': 'today'}, 'today')
        )

        # False - wrong date
        self.assertFalse(
            _to_be_written('aka', {'ao': '5', 'DATE': 'today'}, 'tomorrow')
        )


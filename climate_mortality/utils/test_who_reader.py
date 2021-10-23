'''Tests for noaa_reader.py.

 ~/Documents/UMUC/DATA 670/code (master)
$ python -m unittest utils.test_noaa_reader

'''
from pandas import DataFrame
from random import randint
from unittest import skip, TestCase

from .who_reader import (
    _consolidate_age_columns,
    _consolidate_age_groups,
    _prepare_mortality_df,
    _process_pop_df
)


class WHOTest(TestCase):
    @skip
    def test__consolidate_age_columns(self):
        raise NotImplementedError('Write test.')

    @skip
    def test__consolidate_age_groups(self):
        raise NotImplementedError('Write test.')

    @skip
    def test__prepare_mortality_df(self):
        raise NotImplementedError('Write test.')
    
    @skip
    def test__process_pop_df(self):
        raise NotImplementedError('Write test.')

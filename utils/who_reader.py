'''Read/write utilities for reading WHO ICD-10 mortality CSVs.'''

import pandas as pd

from csv import DictReader, DictWriter

from os import listdir, remove
from os.path import join


def process_WHO(source_dir, dest_dir):
    '''Preprocess WHO mortality data

    * Drop IM mortality data after confirming the entries are either all blank
    or sum to the lowest regular age bracket's deaths (0-1 y.o.).
    * Treat all blanks as zeroes.
    * After ingestion, check the sum across all age groups matches the count in
    the "all ages" column. Reject any rows that do not match, unless the
    all-ages column was blank.
    * Drop rows for which I cannot find a SHP boundary record.
    '''

    countries = pd.read_csv(join(source_dir, 'country_codes.csv'))
    population = pd.read_csv(join(source_dir, 'pop.csv'))

    for fname in listdir(source_dir):
        if fname.endswith('.csv') and fname.startswith('Morticd10'):
            fpath = join(source_dir, fname)
            print(f'Processing {fpath}')
            df = pd.read_csv(fpath)
            

'''Read/write utilities for reading WHO ICD-10 mortality CSVs.'''

import pandas as pd

from csv import DictReader, DictWriter

from os import listdir, remove
from os.path import join


def _process_pop_df(source_dir, dest_dir):
    population = pd.read_csv(join(source_dir, 'pop.csv'))
    filtered = population[population['Year']>=1995]
    # Drop irrelevant columns
    filtered = filtered.to_csv(join(dest_dir, 'pop.csv'))[[
        'Country',
        'Year',
        'Sex',
        'Frmat',
        'Pop1',
        'Pop2',
        'Pop3',
        'Pop4',
        'Pop5',
        'Pop6',
        'Pop7',
        'Pop8',
        'Pop9',
        'Pop10',
        'Pop11',
        'Pop12',
        'Pop13',
        'Pop14',
        'Pop15',
        'Pop16',
        'Pop17',
        'Pop18',
        'Pop19',
        'Pop20',
        'Pop21',
        'Pop22',
        'Pop23',
        'Pop24',
        'Pop25',
        'Pop26',
        'Lb'
    ]]
    filtered = filtered.to_csv(join(dest_dir, 'pop.csv'))
    return filtered

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
    population = _process_pop_df(source_dir, dest_dir)

    composite = None

    for fname in listdir(source_dir):
        if fname.endswith('.csv') and fname.startswith('Morticd10'):
            fpath = join(source_dir, fname)
            print(f'Processing {fpath}')
            mort_df = pd.read_csv(fpath)
            
            

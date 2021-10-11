'''Read/write utilities for reading WHO ICD-10 mortality CSVs.'''

import pandas as pd

from csv import DictReader, DictWriter

from os import listdir, remove
from os.path import join

# Functions with only external dependencies

def _consolidate_age_columns(df, new_col, col_list):
    '''Combine and remove <col_list>, moving all numbers into <new_col>.'''
    df[new_col] = df[col_list[0]]
    del df[col_list[0]]
    n = 1
    
    while n < len(col_list):
        df[new_col] = df[new_col] + df[col_list[n]]
        del df[col_list[n]]
        n += 1
    
    return df

# Functions with internal dependencies

def _consolidate_age_groups(raw_population, prefix='Pop'):
    '''Combine the age columns.'''
    population = _consolidate_age_columns(
        raw_population,
        prefix + '1-4',
        ['Pop3', 'Pop4', 'Pop5', 'Pop6']
    )
    population = _consolidate_age_columns(
        population,
        prefix + '5-14',
        ['Pop7', 'Pop8']
    )
    population = _consolidate_age_columns(
        population,
        prefix + '15-24',
        ['Pop9', 'Pop10']
    )
    population = _consolidate_age_columns(
        population,
        prefix + '25-34',
        ['Pop11', 'Pop12']
    )
    population = _consolidate_age_columns(
        population,
        prefix + '35-44',
        ['Pop13', 'Pop14']
    )
    population = _consolidate_age_columns(
        population,
        prefix + '45-54',
        ['Pop15', 'Pop16']
    )
    population = _consolidate_age_columns(
        population,
        prefix + '55-64',
        ['Pop17', 'Pop18']
    )
    return _consolidate_age_columns(
        population,
        prefix + '65+',
        ['Pop19', 'Pop20','Pop21', 'Pop22', 'Pop23', 'Pop24', 'Pop25']
    )


def _process_pop_df(raw_population):
    '''Process the raw population WHO data.'''
    print('Processing raw population data.')
    population = raw_population[raw_population['Year']>=1995]
    # Drop irrelevant and redundant columns
    del population['Frmat']
    del population['Admin1']
    del population['SubDiv']
    # Aggregate by (Country, Year, Sex) to deduplicate  Admin1 and Subdiv1
    # Blanks are automatically converted to 0.0 by Pandas
    population = population.groupby(['Country', 'Year', 'Sex']).sum()
    # Combine age groups to coarsest age format ("08")
    population = population._consolidate_age_groups(population)
    # TODO: Check sum against "all ages" column Pop1
    # TODO: Handle "Unknown age" column
    return population


def _prepare_mortality_df(raw_mortality):
    '''Process and return the raw mortality data.'''
    mortality = raw_population[raw_mortality['Year']>=1995]
    # Drop irrelevant and redundant columns
    del mortality['Frmat']
    del mortality['IM_Frmat']
    del mortality['IM_Death1']
    del mortality['IM_Death2']
    del mortality['IM_Death3']
    del mortality['IM_Death4']
    del mortality['Admin1']
    del mortality['SubDiv']
    del mortality['List']
    # Aggregate by (Country, Year, Sex) to deduplicate  Admin1 and Subdiv1
    # Blanks are automatically converted to 0.0 by Pandas
    mortality = mortality.groupby(['Country', 'Year', 'Sex', 'Cause']).sum()
    # Combine age groups to coarsest age format ("08")
    mortality = mortality._consolidate_age_groups(population, prefix='Died')
    # TODO: Check sum against "all ages" column Pop1
    # TODO: Handle "Unknown age" column
    # TODO: Handle "IM" columns (infant mortality)
    return mortality


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

    mortality_df_list = []

    for fname in listdir(source_dir):
        if fname.endswith('.csv') and fname.startswith('Morticd10'):
            fpath = join(source_dir, fname)
            print(f'Processing {fpath}')
            mortality_df_list.append(_prepare_mortality_df(pd.read_csv(fpath)))
            
    mortality = pd.concat(mortality_df_list)
    del mortality_df_list
    countries = pd.read_csv(join(source_dir, 'country_codes.csv'))
    population = _process_pop_df(pd.read_csv(join(source_dir, 'pop.csv')))
    mortality = pd.merge(
        left=mortality,
        left_on='Country',
        right=countries,
        right_on='country'
    )
    population = pd.merge(
        left=population,
        on='Country',
        right=countries,
        right_on='country'
    )
    del countries

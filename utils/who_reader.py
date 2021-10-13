'''Read/write utilities for reading WHO ICD-10 mortality CSVs.'''

import pandas as pd

from csv import DictReader, DictWriter

from os import listdir, remove
from os.path import join

from pprint import pformat

'''  # Disabled pyspark because it requires an extra install
from pyspark import SparkContext
from pyspark.sql import DataFrameReader
from pyspark.sql.functions import col
'''

SEX = pd.DataFrame.from_dict([
    {'Sex': 1, 'Gender': 'Male'},
    {'Sex': 2, 'Gender': 'Female'},
    {'Sex': 3, 'Gender': 'Unspecified'}
])
#SPARK = SparkContext()

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

def _consolidate_age_groups(raw_population, prefix):
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
    population = raw_population[raw_population['Year']>=1995].fillna(0)
    # Drop irrelevant and redundant columns
    del population['Frmat']
    del population['Admin1']
    del population['SubDiv']
    # Aggregate by (Country, Year, Sex) to deduplicate  Admin1 and Subdiv1
    population = population.groupby(['Country', 'Year', 'Sex']).sum()
    population = population.reset_index()
    population = pd.merge(on='Sex', left=population, right=SEX)
    # Combine age groups to coarsest age format ("08")
    population = _consolidate_age_groups(population, prefix='Pop')
    # TODO: Check sum against "all ages" column Pop1
    # TODO: Handle "Unknown age" column
    return population


def _prepare_mortality_df(source_mort_paths, dest_dir):
    '''Process and return the raw mortality data.'''
    print('Reading mortality data from {}'.format(pformat(source_mort_paths)))
    source_mort = DataFrameReader(SPARK).csv(path=source_mort_paths[0])
    n = 1
    
    while n < len(source_mort_paths):
        source_mort = source_mort.unionByName(
            DataFrameReader.csv(source_mort_paths[n])
        )
        n += 1

    mortality = source_mort.filter(mortality.Year >= 1995).fillna(0).drop([
        'Frmat',
        'IM_Frmat',
        'IM_Deaths1',
        'IM_Deaths2',
        'IM_Deaths3',
        'IM_Deaths4',
        'Admin1',
        'SubDiv'
    ]).withColumn(
    # Combine age groups to coarsest age format ("08")
        "Deaths1-4",
        col("Deaths3")+col('Deaths4')+col('Deaths5')+col('Deaths6')
    ).withColumn(
        "Deaths5-14",
        col("Deaths7")+col('Deaths8')
    ).withColumn(
        "Deaths15-24",
        col("Deaths10")+col('Deaths9')
    ).withColumn(
        "Deaths25-34",
        col("Deaths12")+col('Deaths11')
    ).withColumn(
        "Deaths35-44",
        col("Deaths14")+col('Deaths13')
    ).withColumn(
        "Deaths45-54",
        col("Deaths16")+col('Deaths15')
    ).withColumn(
        "Deaths55-64",
        col("Deaths18")+col('Deaths17')
    ).withColumn(
        "Deaths65+",
        col("Deaths19")+col('Deaths20')+col('Deaths21')+col('Deaths22')+col('Deaths23')+col('Deaths24')+col('Deaths25')
    ).drop([
        'Deaths3', 'Deaths4', 'Deaths5', 'Deaths6', 'Deaths7', 'Deaths8',
        'Deaths9', 'Deaths10', 'Deaths11', 'Deaths12', 'Deaths13', 'Deaths14',
        'Deaths15', 'Deaths16', 'Deaths17', 'Deaths18', 'Deaths19', 'Deaths20',
        'Deaths21', 'Deaths22', 'Deaths23', 'Deaths24', 'Deaths25'
    # Aggregate by (Country, Year, Sex) to deduplicate  Admin1 and Subdiv1
    ]).groupBy(['Country', 'Year', 'Sex', 'Cause']).agg(
        sum('Deaths1').alias('AllDead'),
        sum('Deaths2').alias('Dead0'),
        sum('Deaths1-4').alias('Dead1-4'),
        sum('Deaths5-14').alias('Dead5-14'),
        sum('Deaths15-24').alias('Dead15-24'),
        sum('Deaths25-34').alias('Dead25-34'),
        sum('Deaths35-44').alias('Dead35-44'),
        sum('Deaths45-54').alias('Dead45-54'),
        sum('Deaths55-64').alias('Dead55-64'),
        sum('Deaths65+').alias('Dead65+'),
        sum('Deaths26').alias('DeadUnknown')
    ).drop([
        'Deaths1',
        'Deaths2',
        'Deaths1-4',
        'Deaths5-14',
        'Deaths15-24',
        'Deaths25-34',
        'Deaths35-44',
        'Deaths45-54',
        'Deaths55-64',
        'Deaths65+',
        'DeathsUnknown'
    ])
    mortality.write.csv(join(dest_dir, 'reformatted_mortality.csv'))
    # Need mortality['List'] to correctly interpret mortality['Cause']
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

    Individual mortality files are too large for in-memory Pandas DataFrames.
    Instead read them as CSVs
    '''
    # Read the names of the countries
    countries = pd.read_csv(join(source_dir, 'country_codes.csv'))
    # Process the raw population counts, via Pandas for simplicity
    population = _process_pop_df(pd.read_csv(join(source_dir, 'pop.csv')))
    population = pd.merge(
        left=population,
        left_on='Country',
        right=countries,
        right_on='country'
    )
    del population['country']
    population = population.rename(columns={'name': 'CountryName'})
    print(population.columns)
    population.to_csv(join(dest_dir, 'population.csv'), index=False)
    source_mort_paths = [
        join(source_dir, fname)
        for fname in listdir(source_dir)
        if fname.endswith('.csv') and fname.startswith('Morticd10')
    ]

    #mortality = _prepare_mortality_df(source_mort_paths, dest_dir)
    
    
    '''
    for fname in listdir(source_dir):
        if fname.endswith('.csv') and fname.startswith('Morticd10'):
            fpath = join(source_dir, fname)
            print(f'Processing {fpath}')
            mortality_df_list.append(_prepare_mortality_df(pd.read_csv(fpath)))
            
    mortality = pd.concat(mortality_df_list)
    del mortality_df_list
    mortality = pd.merge(
        left=mortality,
        left_on='Country',
        right=countries,
        right_on='country'
    )
    mortality.to_csv(join(dest_dir, 'death_counts.csv'), index=False)
    #mortality = pd.merge(
    del countries
    '''

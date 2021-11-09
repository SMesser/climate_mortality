'''Read/write utilities for reading WHO ICD-10 mortality CSVs.'''

import pandas as pd

from csv import DictReader, DictWriter

from os import listdir, remove
from os.path import isfile, join

from pprint import pformat
from sys import stdout
from yaml import safe_load

SEX_DICT = {
    1: 'Male',
    2: 'Female',
    3: 'Unspecified'
}
SEX = pd.DataFrame.from_dict([
    {'Sex': n, 'Gender': s}
    for n, s in SEX_DICT.items()
])


with open('./files.yaml', 'r') as fp:
    settings = safe_load(fp)


def _collect_causes():
    '''Scan all processed WHO country files to assemble distinct causes.'''
    country_dir = settings['who']['country_output_dir']
    causes = set()
    
    for fname in listdir(country_dir):
        print(f'Scanning {fname}')
        causes = causes | set(pd.read_csv(join(country_dir, fname))['Cause'])

    return sorted(causes)
    

def _trim_country_file_to_cause(country_file, cause):
    '''Remove all columns and records not matchnig the cause from the file.'''
    raw_df = pd.read_csv(country_file)
    return raw_df[raw_df['Cause']==cause][[
        'CountryName',
        'Gender',
        'MortAll',
        'Mort0',
        'Mort1-4',
        'Mort5-14',
        'Mort15-24',
        'Mort25-34',
        'Mort35-44',
        'Mort45-54',
        'Mort55-64',
        'Mort65+',
        'MortUnk',
    ]]
    

def convert_country_tables_to_causes():
    '''Convert country_output_dir files to cause_output_dir.'''
    causes = _collect_causes()
    country_dir = settings['who']['country_output_dir']
    cause_dir = settings['who']['cause_output_dir']
    country_files = listdir(country_dir)
    
    for cause in causes:
        cause_df = pd.concat([
            _trim_country_file_to_cause(join(country_dir, fname), cause)
            for fname in country_files
        ])
        cause_df.to_csv(join(cause_dir, cause + '_mortality.csv'), index=False)

    
def load_cause_for_file(path, cause):
    '''Create a DF with the overall mortality''' 
    base = pd.read_csv(path)
    base = base[base['Cause']==cause]
    # Sum over values of Sex and return the result
    return base[['CountryName', 'MortAll', 'Year']].groupby(
        by=('CountryName', 'Year'),
        as_index=False
    ).sum()
    

def load_WHO_mortality(country, years):
    mort = pd.read_csv(
        join(settings['who']['country_output_dir'], f'{country}_mortality.csv')
    )


def load_cause(cause):
    '''Load the full set of mortality metrics for a given cause of death.'''
    mort_dir = settings['who']['country_output_dir']
    df_list = [
        load_cause_for_file(join(mort_dir, fn))
        for fn in listdir(mort_dir)
        if fn.endswith('_mortality.csv')
    ]
    return pd.concat(df_list)


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


def _prepare_mortality_df(source_mort_paths, dest_dir, population, causes):
    '''Process and return the raw mortality data.'''
    # Create reference list of columns that are safe to convert to numbers.
    numerical_columns = [
        'Year',
        'Sex'
    ] + [f'Deaths{n}' for n in range(1, 27)]
    suffixes = [
        'All',
        '0',
        '1-4',
        '5-14',
        '15-24',
        '25-34',
        '35-44',
        '45-54',
        '55-64',
        '65+',
        'Unk'
    ]
    print('Reading mortality data from {}'.format(pformat(source_mort_paths)))
    
    for country_num in set(population['Country']):
        country_name = set(
            population[population['Country']==country_num]['CountryName']
        ).pop()
        print(f'Aggregating {country_name} (#{country_num}) data.')
        stdout.flush()
        records = []
        
        for filename in source_mort_paths:
            print(f'Checking {filename}')
            
            with open(filename, 'r') as fp:
                reader = DictReader(fp)
                
                # Filter the source file and drop columns we don't need.
                for row in reader:
                    if int(row['Country']) == int(country_num):
                        list_cause = '{}-{}'.format(
                            row['List'],
                            row['Cause']
                        )
                        row = { # convert blanks to 0
                            k: float(row[k]) if row[k] else 0
                            for k in numerical_columns
                        }
                        records.append({
                            'Country': country_num,
                            'CountryName': country_name,
                            'Year': row['Year'],
                            'ListCause': list_cause,
                            'Gender': SEX_DICT.get(row['Sex'], 'Unspecified'),
                            'DeathsAll': row['Deaths1'],
                            'Deaths0': row['Deaths2'],
                            'Deaths1-4': row['Deaths3'] + row['Deaths4'] + row['Deaths5'] +row['Deaths6'],
                            'Deaths5-14': row['Deaths7'] + row['Deaths8'],
                            'Deaths15-24': row['Deaths9'] + row['Deaths10'],
                            'Deaths25-34': row['Deaths11'] + row['Deaths12'],
                            'Deaths35-44': row['Deaths13'] + row['Deaths14'],
                            'Deaths45-54': row['Deaths15'] + row['Deaths16'],
                            'Deaths55-64': row['Deaths17'] + row['Deaths18'],
                            'Deaths65+': row['Deaths19'] + row['Deaths20'] + row['Deaths21'] + row['Deaths22'] + row['Deaths23'] + row['Deaths24'] + row['Deaths25'],
                            'DeathsUnk': row['Deaths26']
                        })
        
        output_path = join(dest_dir, '{}_mortality.csv'.format(country_name))

        if len(records) > 0:
            print(f'Found {len(records)} death records.')
            dead = pd.DataFrame.from_dict(records)
            dead = pd.merge(
                left=dead,
                on=('CountryName', 'Year', 'Country', 'Gender'),
                right=population
            )
            dead.rename(
                columns={'Pop1': 'PopAll', 'Pop2': 'Pop0', 'Pop26': 'PopUnk'},
                inplace=True
            )
            
            for suffix in suffixes:
                dead['Mort'+suffix] = dead['Deaths'+suffix]/dead['Pop'+suffix]

            mort = pd.merge(left=dead, on='ListCause', right=causes, how='left')
            mort['Cause'] = mort['Cause'].where(
                mort['Cause'].notnull(),
                other=mort['ListCause']
            )
            if mort.shape[0] > 0:
                print(
                    f'Writing {mort.shape[0]} records and {mort.shape[1]} columns.'
                ) 
                del mort['List']
                del mort['Code']
                del mort['Detailed code']
                mort.to_csv(
                    output_path,
                    index=False
                )
            else:
                print(
                    'Failed to recognize any codes for {} (#{}): e.g. {}'.format(
                        country_name,
                        country_num,
                        list(set(dead['ListCause']))[:10]
                    )
                )
                if isfile(output_path):
                    remove(output_path)
        else:
            print(f'Found no records for {country_name}')
            if isfile(output_path):
                remove(output_path)
    # Need mortality['List'] to correctly interpret mortality['Cause']
    # TODO: Check sum against "all ages" column Pop1
    # TODO: Handle "IM" columns (infant mortality)


def process_WHO_pop(source_dir, dest_dir, supp_dir):
    '''Preprocess WHO population data

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


def process_WHO_dead(source_dir, dest_dir, supp_dir):
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
    # Process the raw population counts, via Pandas for simplicity
    population = pd.read_csv(join(dest_dir, 'population.csv'))
    source_mort_paths = [
        join(source_dir, fname)
        for fname in listdir(source_dir)
        if fname.endswith('.csv') and fname.startswith('Morticd10')
    ]
    causes = pd.read_csv(join(supp_dir, 'WHOCauseCodes.csv'))
    _prepare_mortality_df(
        source_mort_paths,
        dest_dir,
        population,
        causes
    )

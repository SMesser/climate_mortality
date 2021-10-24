'''This file includes scripts intended to generate plots for output.

Plotly figures can be saved to JPG interactively through the browser, but saving
them programmatically requires installing an "orca" executable.
'''
import pandas as pd

from numpy import mean
from os.path import join
from sys import stdout
from yaml import safe_load

from .noaa_reader import DATA_COLUMNS, load_compiled_NOAA

with open('./files.yaml', 'r') as fp:
    settings = safe_load(fp)


def load_interpolated_NOAA(var, year, month):
    '''Load NOAA data for a single variable in a given month.'''
    return pd.read_csv(
        join(settings['noaa']['interpolated_dir'], f'{var}{year}-{month}.csv')
    )


def annualize_NOAA(var, year):
    '''Create 2D annualized map across available per-month interpolations.'''
    # Make a list of all the columns we will use.
    columns = [
        f'{var}_{month}'
        for month in range(1, 13)
    ]

    # Compile & join all interpolations
    base = load_interpolated_NOAA(
        var=var,
        year=year,
        month=1
    ).rename(columns={var: f'{var}_1'})
    
    for month in range(2, 13):
        additional = load_interpolated_NOAA(var=var, year=year, month=month)
        base = pd.merge(
            left=base,
            right=additional,
            on=['LONGITUDE', 'LATITUDE'],
            suffixes=[None, f'_{month}']
        )

    base['min'] = base[columns].apply(min, axis=1)
    base['max'] = base[columns].apply(max, axis=1)
    base['mean'] = base[columns].apply(mean, axis=1)

    # Remove the component columns after annualization
    for col in columns:
        del base[col]

    # Write the result to a file
    base.to_csv(join(settings['noaa']['annualized_dir'], f'{year}'))
    return base


def annualize_all_NOAA():
    '''Loop over NOAA data, doing annualization stage of processing.

    Loop over all variables and years to annualiz and store all NOAA
    data.
    '''
    for var in INTERPOLATION_COLUMNS:
        print(f'------Annualizing for {var}')
        for year in range(1995, 2022):
            print(f'##Annualizing for {var}{year}')
            stdout.flush()
            try:
                annualized = annualize_NOAA(var, year)
            except FileNotFoundError as exc:
                print(f'Missing data for {var}{year}: {exc}')
            else:
                annualized.to_csv(
                    join(
                        settings['noaa']['annualized_dir'],
                        f'{var}{year}-{month}.csv'
                    ),
                    index=False
                )

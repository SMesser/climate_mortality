'''This file includes scripts intended to annualize NOAA interpolations.

The primary purpose of interpolation is to make Northern- and Southern-
-hemisphere climates look the same when the only difference between them is
the timing of their peak & nadir temperatures. It also reduces the amount of
redundant data, as temperature and precipitation shift smoothly between
extremes.
'''
import pandas as pd

from numpy import mean
from os.path import join
from scipy.interpolate import interp2d
from sys import stdout
from yaml import safe_load

from .interpolation import INTERPOLATION_COLUMNS, load_interpolated_NOAA

with open('./files.yaml', 'r') as fp:
    settings = safe_load(fp)


def load_annualized_NOAA(var, year):
    '''Load NOAA data for a single variable in a given year.'''
    return pd.read_csv(
        join(settings['noaa']['annualized_dir'], f'{var}{year}.csv')
    )


def interpolate_annualized_NOAA(var, year, points, kind='linear'):
    sample_df = load_annualized_NOAA(var, year)
    func_min = interp2d(
        x=sample_df['LONGITUDE'],
        y=sample_df['LATITUDE'],
        z=sample_df['min'],
        kind=kind,
    )
    func_mean = interp2d(
        x=sample_df['LONGITUDE'],
        y=sample_df['LATITUDE'],
        z=sample_df['mean'],
        kind=kind,
    )
    func_max = interp2d(
        x=sample_df['LONGITUDE'],
        y=sample_df['LATITUDE'],
        z=sample_df['max'],
        kind=kind,
    )
    return pd.DataFrame.from_dict([
        {
            'LONGITUDE': p[0],
            'LATITUDE': p[1],
            var+ '_min': func_min(p[0], p[1]),
            var+ '_mean': func_mean(p[0], p[1]),
            var+ '_max': func_max(p[0], p[1]),
        }
        for p in points
    ])


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
        additional = load_interpolated_NOAA(
            var=var,
            year=year,
            month=month
        ).rename(columns={var: f'{var}_{month}'})
        base = pd.merge(
            left=base,
            right=additional,
            on=['LONGITUDE', 'LATITUDE'],
        )

    base['min'] = base[columns].apply(min, axis=1)
    base['max'] = base[columns].apply(max, axis=1)
    base['mean'] = base[columns].apply(mean, axis=1)

    # Remove the component columns after annualization
    for col in columns:
        del base[col]

    return base


def annualize_all_NOAA():
    '''Loop over NOAA data, doing annualization stage of processing.

    Loop over all variables and years to annualiz and store all NOAA
    data.
    '''
    for var in INTERPOLATION_COLUMNS:
        print(f'------ Annualizing for {var}')
        for year in range(1995, 2022):
            print(f'## Annualizing for {var}{year}')
            stdout.flush()
            try:
                annualized = annualize_NOAA(var, year)
            except FileNotFoundError as exc:
                print(f'Missing data for {var}{year}: {exc}')
            else:
                annualized.to_csv(
                    join(
                        settings['noaa']['annualized_dir'],
                        f'{var}{year}.csv'
                    ),
                    index=False
                )

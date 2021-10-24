'''This file includes scripts intended to generate plots for output.

Plotly figures can be saved to JPG interactively through the browser, but saving
them programmatically requires installing an "orca" executable.
'''
import pandas as pd

from numpy import array, nan
from os.path import join
from scipy.interpolate import griddata
from sys import stdout
from yaml import safe_load

from .noaa_reader import DATA_COLUMNS, load_compiled_NOAA


INTERPOLATION_COLUMNS = DATA_COLUMNS.union({'HUMID'})


with open('./files.yaml', 'r') as fp:
    settings = safe_load(fp)

##### utility functions #####


def _interpolate_HUMID(year, month, kind):
    '''Generate a HUMIDITY proxy in mm-degrees Celsius.'''
    tavg_df = _interpolate_NOAA(var='TAVG', year=year, month=month, kind=kind)
    prcp_df = _interpolate_NOAA(var='PRCP', year=year, month=month, kind=kind)
    humid_df = tavg_df.merge(prcp_df, on=['LONGITUDE', 'LATITUDE'])
    # Not much difference if we use TAVG or Kelvin as proxy for humidity.
    #humid_df['Kelvin'] = humid_df['TAVG']+273.15
    #humid_df['HUMID'] = humid_df['PRCP']*humid_df['Kelvin']
    # humid_df['HUMID'] = humid_df['PRCP']*humid_df['TAVG']
    # Actual important variable is human heat stress - may want to subtract a temperature
    # like 20 Celsius
    humid_df['human'] = humid_df['TAVG']-20 # Approx optimal human environment temperature
    humid_df['HUMID'] = humid_df['PRCP']*humid_df['human']
    return humid_df


def _interpolate_NOAA(var, year, month, kind):
    '''Generate a map of NOAA data .

    Possible enhancement to get better coverage of mid-Pacific and high latitudes would be to extend
    the data set to east and west by copying it over with +360 and -360 degree adjustments to the longitude.
    However, since the affected areas have low populations, the effect this would have on predictions for cities is minimal.
    Also, the resulting values for the affected areas would be interpolated between a small number of independent,
    widely-separated points.
    '''
    source_df = load_compiled_NOAA(var=var, month=month, year=year).to_dict('records')
    points = array([
        [record['LONGITUDE'], record['LATITUDE']]
        for record in source_df
    ])
    values = array([
        record[var]
        for record in source_df
    ])
    xi = array([
        [x, y]
        for x in range(-180, 180)
        for y in range(-90, 90)
    ])
    interpolated = griddata(
        points,
        values,
        xi,
        method=kind,
    )
    return pd.DataFrame.from_dict([
        {'LONGITUDE': xi[n][0], 'LATITUDE': xi[n][1], var: interpolated[n]}
        for n in range(len(xi))
    ]).dropna()

def interpolate_NOAA(var, year, month, kind='linear'):
    '''Create 2D interpolated map across available observations.

    <kind> is one of {'nearest', 'linear', 'cubic'}, according to the desired
    order of the interpolating piecewise polynomial. The default is 'linear'.
    
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.interp2d.html
    '''
    if var=='HUMID':
        return _interpolate_HUMID(year, month, kind=kind)
    else:
        return _interpolate_NOAA(var, year, month, kind=kind)


def interpolate_all_NOAA(method='linear'):
    '''Loop over NOAA data, doing interpolation stage of processing.

    Loop over all variables, months, and years to interpolate and store all NOAA
    data.
    '''
    for var in INTERPOLATION_COLUMNS:
        print(f'------Interpolating for {var}')
        for year in range(1995, 2022):
            print(f'##Interpolating for {var}{year}')
            for month in range(1, 13):
                print(f'Interpolating for {var}{year}-{month}')
                stdout.flush()
                try:
                    interpolated = interpolate_NOAA(
                        var=var,
                        year=year,
                        month=month,
                        kind=method
                    )
                except FileNotFoundError as exc:
                    print(f'Missing data for {var}{year}-{month}: {exc}')
                else:
                    interpolated.to_csv(
                        join(
                            settings['noaa_interpolated_dir'],
                            f'{var}{year}-{month}.csv'
                        ),
                        index=False
                    )

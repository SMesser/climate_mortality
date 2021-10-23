'''This file includes scripts intended to generate plots for output.

Plotly figures can be saved to JPG interactively through the browser, but saving
them programmatically requires installing an "orca" executable.
'''
import pandas as pd

from numpy import array
from os.path import join
from scipy.interpolate import griddata
from yaml import safe_load

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
    ])

def interpolate_NOAA(var, year, month, kind='linear'):
    '''Create 2D interpolated map across available observations.

    <kind> is one of {'nearest', 'linear', 'cubic'}, according to the desired
    order of the interpolating piecewise polynomial. The default is 'linear'.
    
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.interp2d.html
    '''
    # TODO: SOMETHING HERE IS CAUSING VERY LARGE VALUES TO BE RETURNED AND
    # CONSUMING RIDICULOUS AMOUNTS OF MEMORY.  WHY?
    if var=='HUMID':
        return _interpolate_HUMID(year, month, kind=kind)
    else:
        return _interpolate_NOAA(var, year, month, kind=kind)


def plot_interpolated(var, month, year, kind='linear'):
    '''Plot interpolated NOAA data.'''
    df = interpolate_NOAA(var, year=year, month=month, kind=kind)
    fig = go.Figure(
        data=go.Scattergeo(
            lon=df['LONGITUDE'],
            lat=df['LATITUDE'],
            text=df[var],
            mode='markers',
            marker_color=df[var],
            marker={
                'colorscale': get_NOAA_colorscale(var),
                'showscale': True
            },
            opacity=0.7,
        ),
        layout={
            'title': {'text': make_NOAA_title(var, year, month)},
        }
    ).show()
    

def plot_NOAA_interp():
    # Choose linear interpolation because cubic gives some wild swings outside the observed range,
    # to average temperatures as high as 2500 and as low as -2000 Celsius. These are presumably due
    # to closely-spaced observations with different climates, such as near the top and foot of high mountains.
    #plot_interpolated('TAVG', year=2015, month=7, kind='linear')
    #plot_interpolated('EMNT', year=2015, month=7)
    #plot_interpolated('EMXT', year=2015, month=7)
    plot_interpolated('HUMID', year=2015, month=7)


'''This file includes scripts intended to generate plots for output.

Plotly figures can be saved to JPG interactively through the browser, but saving
them programmatically requires installing an "orca" executable.
'''
import pandas as pd
import plotly.graph_objects as go

from os.path import join
from yaml import safe_load

VAR2FILE = {
    'PRCP': 'prec_{month}.csv',
    'TMIN': 'tmin_{month}.csv',
    'TMAX': 'tmax_{month}.csv',
    'TAVG': 'tmean_{month}.csv',
}

with open('./files.yaml', 'r') as fp:
    settings = safe_load(fp)

##### utility functions #####
def load_CMIP5(directory, fname):
    '''Load CMIP5 data for a single variable in a given month.'''
    return pd.read_csv(
        join(settings['cmip5']['output_dir'], directory, fname)
    )


def make_CMIP5_title(var, decade, month):
    fmt_dict = {
        "EMNT": 'Lowest recorded temperature for {month} in Celsius during the {decade}s',
        "PRCP": 'Total precipitation for {month} in mm during the {decade}s',
        "TAVG": 'Average temperature for {month} in degrees Celsius during the {decade}s',
        "EMXT": 'Highest recorded temperature for {month} in Celsius during the {decade}s',
        "TMAX": 'Average daily high temperature for {month} in Celsius during the {decade}s',
        "TMIN": 'Average daily low temperature for {month} in Celsius during the {decade}s',
    }
    month_dict = [
        'January',
        'February',
        'March',
        'April',
        'May',
        'June',
        'July',
        'August',
        'September',
        'October',
        'November',
        'December'
    ]
    return fmt_dict[var].format(month=month_dict[month-1], decade=decade)


def get_CMIP5_colorscale(var):
    '''Choose a colorscale which visually corresponds to the given variable.'''
    if var=='PRCP':
        # list several options but only return one
        return ['ylgn', 'speed', 'bluyl'][2]
    else:
        return 'bluered'

##### direct-output data-plot functions #####

def plot_CMIP5_var(directory, var, month):
    '''Plot global CMIP5 data for a single variable in a given month.'''
    fname = VAR2FILE[var].format(month=month)
    df = load_CMIP5(directory, fname)
    fig = go.Figure(
        data=go.Scattergeo(
            lon=df['LONGITUDE'],
            lat=df['LATITUDE'],
            text=df[var],
            mode='markers',
            marker_color=df[var],
            marker={
                'colorscale': get_CMIP5_colorscale(var),
                'showscale': True
            },
        ),
        layout={
            'title': {'text': make_CMIP5_title(var, '2030', month)},
            'xaxis': {'range': [-65, -125]},
            'yaxis': {'range': [24, 50]},
            'margin': {"r":0,"t":0,"l":0,"b":0},
            'geo': {
                'lonaxis_range': [-126, -64],
                'lataxis_range': [23, 51],
                'showlakes': True,
                'showrivers': True,
            },
        }
    ).show()


def _plot_one_CMIP5_sample(dataset, var, month):
    directory = join(
        settings['cmip5']['output_dir'],
        dataset,
    )
    plot_CMIP5_var(directory, var, month)

def plot_CMIP5_samples():
    '''A collection of several CMIP5 datasets demonstrating data breadth.'''
    # cccma_canesm2_rcp4_5_2030s_prec_30s_r1i1p1_b2_asc dataset was used in
    # early drafts, but hs been dropped due to excessively high resolution
    # and the resulting large size of the dataset.
    #_plot_one_CMIP5_sample(
    #    'cccma_canesm2_rcp4_5_2030s_prec_30s_r1i1p1_b2_asc\\prec_b2',
    #    'PRCP',
    #    7
    #)
    _plot_one_CMIP5_sample(
        'cesm1_cam5_rcp4_5_2030s_prec_10min_r1i1p1_no_tile_asc',
        'PRCP',
        6
    )
    _plot_one_CMIP5_sample(
        'cccma_canesm2_rcp8_5_2050s_tmax_10min_r1i1p1_no_tile_asc',
        'TMAX',
        7
    )
    _plot_one_CMIP5_sample(
        'csiro_mk3_6_0_rcp4_5_2050s_tmin_10min_r1i1p1_no_tile_asc',
        'TMIN',
        8
    )
    _plot_one_CMIP5_sample(
        'gfdl_esm2g_rcp8_5_2050s_tmean_10min_r1i1p1_no_tile_asc',
        'TAVG',
        9
    )

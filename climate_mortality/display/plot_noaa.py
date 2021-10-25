'''This file includes scripts intended to generate plots for output.

Plotly figures can be saved to JPG interactively through the browser, but saving
them programmatically requires installing an "orca" executable.
'''
import pandas as pd
import plotly.graph_objects as go

from numpy import array
from os.path import join
from scipy.interpolate import griddata
from yaml import safe_load

from ..utils import load_annualized_NOAA, load_interpolated_NOAA, load_compiled_NOAA

with open('./files.yaml', 'r') as fp:
    settings = safe_load(fp)

MONTH_NAMES = {
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September',
    10: 'October',
    11: 'November',
    12: 'December'
}

##### utility functions #####

def make_NOAA_raw_title(var, year, month):
    fmt_dict = {
        "EMNT": 'Lowest recorded temperature for {month} {year} in degrees Celsius',
        "PRCP": 'Total precipitation for {month} {year} in mm',
        "TAVG": 'Average temperature for {month} {year} in degrees Celsius',
        "EMXT": 'Highest recorded temperature for {month} {year} in degrees Celsius',
        "TMAX": 'Average daily high temperature for {month} {year} in degrees Celsius',
        "TMIN": 'Average daily low temperature for {month} {year} in degrees Celsius',
        "HUMID": 'Proxy for humidity from average temperature * precipitation in mm-degrees for {month} {year}',
        "HETSTRS": 'Proxy for heat stress from average temperature * precipitation in mm-degrees for {month} {year}',
    }
    return fmt_dict[var].format(year=year, month=MONTH_NAMES[month])


def make_NOAA_annual_title(var, year, column):
    fmt_dict = {
        ("EMNT", 'min'): 'Lowest recorded temperature for {year} in degrees Celsius',
        ("EMNT", 'mean'): 'Average monthly minimum temperature for {year} in degrees Celsius',
        ("EMNT", 'max'): 'Highest monthly minimum temperature for {year} in degrees Celsius',
        ("PRCP", 'min'): 'Total precipitation for driest month of {year} in mm',
        ("PRCP", 'mean'): 'Average precipitation per month for {year} in mm',
        ("PRCP", 'max'): 'Total precipitation for wettest month of {year} in mm',
        ("TAVG", 'min'): 'Average temperature for coldest month of {year} in degrees Celsius',
        ("TAVG", 'mean'): 'Average temperature for {year} in degrees Celsius',
        ("TAVG", 'max'): 'Average temperature for hottest month of {year} in degrees Celsius',
        ("EMXT", 'min'): 'Lowest monthly maximum temperature for {year} in degrees Celsius',
        ("EMXT", 'mean'): 'Average monthly maximum temperature for {year} in degrees Celsius',
        ("EMXT", 'max'): 'Highest recorded temperature for {year} in degrees Celsius',
        ("TMAX", 'min'): 'Average daily high temperature for coldest month of {year} in degrees Celsius',
        ("TMAX", 'mean'): 'Average daily high temperature for {year} in degrees Celsius',
        ("TMAX", 'max'): 'Average daily high temperature for hottest month of {year} in degrees Celsius',
        ("TMIN", 'min'): 'Average daily low temperature for coldest month of {year} in degrees Celsius',
        ("TMIN", 'mean'): 'Average daily low temperature for {year} in degrees Celsius',
        ("TMIN", 'max'): 'Average daily low temperature for hottest month of {year} in degrees Celsius',
        ("HUMID", 'min'): 'Min Proxy for humidity from temperature * precipitation in mm-degrees for {year}',
        ("HUMID", 'mean'): 'Average Proxy for humidity from temperature * precipitation in mm-degrees for {year}',
        ("HUMID", 'max'): 'Max Proxy for humidity from temperature * precipitation in mm-degrees for {year}',
        ("HETSTRS", 'min'): 'Min Proxy for heat stress from temperature * precipitation in mm-degrees for {year}',
        ("HETSTRS", 'mean'): 'Average Proxy for heat stress from temperature * precipitation in mm-degrees for {year}',
        ("HETSTRS", 'max'): 'Max Proxy for heat stress from temperature * precipitation in mm-degrees for {year}',
    }
    return fmt_dict[(var, column)].format(year=year)


def get_NOAA_colorscale(var):
    '''Choose a colorscale which visually corresponds to the given variable.'''
    if var=='PRCP':
        # list several options but only return one
        return ['ylgn', 'speed', 'bluyl'][2]
    elif var=='HUMID':
        return 'portland'
    else:
        return 'bluered'

##### direct-output data-plot functions #####

def plot_NOAA_var(var, year, month):
    '''Plot global NOAA data for a single variable in a given month.'''
    df = load_compiled_NOAA(var, year, month)
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
        ),
        layout={
            'title': {'text': make_NOAA_raw_title(var, year, month)}
        }
    ).show()


def plot_NOAA_samples():
    '''A collection of several NOAA datasets demonstrating data breadth.'''
    plot_NOAA_var('PRCP', 1995, 10)
    plot_NOAA_var('EMNT', 2013, 7)
    plot_NOAA_var('TAVG', 1998, 8)
    plot_NOAA_var('TMIN', 2001, 11)
    plot_NOAA_var('TMAX', 1997, 9)
    plot_NOAA_var('EMXT', 1999, 4)
    plot_NOAA_var('PRCP', 1995, 7)
    plot_NOAA_var('TAVG', 1995, 7)
    plot_NOAA_var('TAVG', 2015, 7)


def plot_interpolated(var, month, year):
    '''Plot interpolated NOAA data.'''
    df = load_interpolated_NOAA(var, year=year, month=month)
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
            'title': {'text': make_NOAA_raw_title(var, year, month)},
        }
    ).show()
    

def plot_NOAA_interp():
    plot_interpolated('TAVG', year=2015, month=7)
    plot_interpolated('EMNT', year=2015, month=7)
    plot_interpolated('EMXT', year=2015, month=7)
    plot_interpolated('HUMID', year=2015, month=7)
    plot_interpolated('HETSTRS', year=2015, month=7)


def plot_annualized(var, year, column):
    '''Plot annualized NOAA data.

    The "column" input should be "max", "min", or "mean".
    '''
    df = load_annualized_NOAA(var, year=year)
    fig = go.Figure(
        data=go.Scattergeo(
            lon=df['LONGITUDE'],
            lat=df['LATITUDE'],
            text=df[column],
            mode='markers',
            marker_color=df[column],
            marker={
                'colorscale': get_NOAA_colorscale(var),
                'showscale': True
            },
            opacity=0.7,
        ),
        layout={
            'title': {'text': make_NOAA_annual_title(var, year, column)},
        }
    ).show()
    

def plot_NOAA_annualized():
    plot_annualized('TAVG', year=2015, column='min')
    plot_annualized('EMNT', year=2015, column='mean')
    plot_annualized('EMXT', year=2015, column='max')
    plot_annualized('HUMID', year=2015, column='mean')
    plot_annualized('HETSTRS', year=2015, column='max')


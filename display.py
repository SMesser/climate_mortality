'''This file includes scripts intended to generate plots for output.

Plotly figures can be saved to JPG interactively through the browser, but saving
them programmatically requires installing an "orca" executable.
'''
import pandas as pd
import plotly.graph_objects as go

from os.path import join
from yaml import safe_load

with open('./files.yaml', 'r') as fp:
    settings = safe_load(fp)

##### utility functions #####

# NOAA utils

def load_NOAA(var, year, month):
    '''Load NOAA data for a single variable in a given month.'''
    return pd.read_csv(
        join(settings['noaa_output_dir'], f'{var}{year}-{month}.csv')
    )


def make_NOAA_title(var, year, month):
    fmt_dict = {
        "EMNT": 'Lowest recorded temperature for {month} {year} in degrees Celsius',
        "PRCP": 'Total precipitation for {month} {year} in mm',
        "TAVG": 'Average temperature for {month} {year} in degrees Celsius',
        "EMXT": 'Highest recorded temperature for {month} {year} in degrees Celsius',
        "TMAX": 'Average daily high temperature for {month} {year} in degrees Celsius',
        "TMIN": 'Average daily low temperature for {month} {year} in degrees Celsius',
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
    return fmt_dict[var].format(year=year, month=month_dict[month-1])


def get_NOAA_colorscale(var):
    '''Choose a colorscale which visually corresponds to the given variable.'''
    if var=='PRCP':
        # list several options but only return one
        return ['ylgn', 'speed', 'bluyl'][2]
    else:
        return 'bluered'

# WHO utils

def _get_WHO_population_df():
    processed_dir = settings['who_output_dir']
    population = pd.read_csv(join(processed_dir, 'population.csv'))
    del population['Sex']
    del population['Country']
    return population

##### direct-output data-plot functions #####

# NOAA data
def plot_NOAA_var(var, year, month):
    '''Plot global NOAA data for a single variable in a given month.'''
    df = load_NOAA(var, year, month)
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
            'title': {'text': make_NOAA_title(var, year, month)}
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

# WHO data

def plot_WHO_pop_growth(countries=None, years=None, barmode='group'):
    '''Plot total population for multiple years and countries'''
    pop = _get_WHO_population_df()
    df = pop.groupby(
        ['CountryName', 'Year']
    ).sum().reset_index()[['CountryName', 'Year', 'Pop1']]

    if countries is None:
        country_list = sorted(set(df['CountryName']))
    else:
        country_list = sorted(countries)
    
    if years is not None:
        df = df[df['Year'].isin(years)]
        
    go.Figure(
        data=[
            go.Bar(
                x=df[df['CountryName']==name]['Year'],
                y=df[df['CountryName']==name]['Pop1'],
                name=name
            )
            for name in country_list
        ],
        layout={
            'title': {'text': 'Population by year and country.'},
            'barmode': barmode
        }
    ).show()


def plot_WHO_samples():
    '''Plot representative slices of WHO data.'''
    plot_WHO_pop_growth(barmode='stack')
    plot_WHO_pop_growth(countries=['Brazil', 'China', 'India', 'United States of America', 'Russian Federation'])

    
def plot_WHO_chloropleth(cause, year):
    '''Compare global death rates for a single cause of death in a year.'''
    raise NotImplementedError('Fill in this function.')


def plot_WHO_bar(cause, year):
    '''Compare global death rates for a single cause of death in a year.'''
    raise NotImplementedError('Fill in this function.')


def plot_WHO_death_bar(df, countries):
    '''Plot raw death counts''' 
    go.Figure(
        data=[
            go.Bar(
                name=c + ' ' + s,
                x=df[df['name']==c][df['Gender']==s]['Year'],
                y=df[df['name']==c][df['Gender']==s]['Deaths1']
                #color={'Male': 'blue', 'Female': 'red', 'Unknown': 'green'}[s]
            )
            for c in ['Russian Federation', 'Ukraine']
            for s in ['Male', 'Female']
        ],
        layout={'title': {'text': 'Malaria deaths'}}
    ).show()


##### Script entry point #####

if __name__ == '__main__':
    with open('./files.yaml', 'r') as fp:
        settings = safe_load(fp)

    # Comment out plots which don't need to be regenerated.
    # plot_NOAA_samples()
    # plot_WHO_samples()
    plot_NOAA_var('PRCP', 1995, 10)
    plot_NOAA_var('TAVG', 1995, 10)
    plot_NOAA_var('PRCP', 2015, 10)
    

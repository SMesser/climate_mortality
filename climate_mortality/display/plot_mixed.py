'''This file includes scripts intended to generate plots for output.

Plotly figures can be saved to JPG interactively through the browser, but saving
them programmatically requires installing an "orca" executable.
'''
import pandas as pd
import plotly.graph_objects as go

from os.path import join
from yaml import safe_load

from ..utils.connect_noaa_who import load_country_climate_df

with open('./files.yaml', 'r') as fp:
    settings = safe_load(fp)

VAR_DESCRIPTIONS = {
    "TMIN": 'Monthly average of daily low temperatures (C)',
    "TAVG": 'Monthly average temperature (C)',
    "TMAX": 'Monthly average of daily high temperatures (C)',
    "PRCP": 'Monthly total precipitation (mm)',
    "HUMID": 'Monthly proxy for humidity (mm-K)',
    "HETSTRS": 'Monthly proxy for heat stress (mm-K)',
}


def plot_single_country_var(country, var):
    '''Plot one country's variation in a single climate variation over time.'''
    df = load_country_climate_df()[[
        'country',
        var+'_min',
        var+'_mean',
        var+'_max',
        'Year',
    ]]
    # Next line is useful if looking for a specific country but unsure of the
    # name it's given in the dataset.
    # print(sorted(set(df['country'])))
    df = df[df['country']==country][[
        var+'_min',
        var+'_mean',
        var+'_max',
        'Year',
    ]]
    descrip = VAR_DESCRIPTIONS[var]
    go.Figure(
        data=[
            go.Scatter(
                x=df['Year'],
                y=df[var + '_min'],
                name='Annual minimum',
                mode='lines',
                line={'color': 'black'},
            ),
            go.Scatter(
                x=df['Year'],
                y=df[var + '_mean'],
                name='Annual average',
                mode='lines',
                line={'color': 'blue'},
            ),
            go.Scatter(
                x=df['Year'],
                y=df[var + '_max'],
                name='Annual maximum',
                mode='lines',
                line={'color': 'black'},
            )
        ],
        layout={
            'title': {'text': f'{descrip} for {country}'},
        }
    ).show()


def plot_country_comparisons(base_var, aggregation='mean', countries=None):
    '''Compare all countries and years for a specific variable.

    Optional input <aggregation> defaults to 'mean', but can be 'min', 'mean',
    or 'max'.
    '''
    var = base_var + '_' + aggregation
    df = load_country_climate_df()[[
        'country',
        'Year',
        var
    ]]
    
    if countries is None:
        countries = sorted(set(df['country']))

    long_agg_name = {
        'min': 'Annual minimum of ' + VAR_DESCRIPTIONS[base_var],
        'mean': 'Annual average of ' + VAR_DESCRIPTIONS[base_var],
        'max': 'Annual maximum of ' + VAR_DESCRIPTIONS[base_var],
    }
    go.Figure(
        data=[
            go.Scatter(
                x=df[df['country']==country]['Year'],
                y=df[df['country']==country][var],
                name=country,
                mode='lines',
            )
            for country in countries
        ],
        layout={
            'title': {'text': long_agg_name[aggregation]},
        }
    ).show()


def plot_country_var_histories():
    '''Plot histories for a single country and variable.'''
    plot_single_country_var('Cuba', 'TMIN')
    plot_single_country_var('Canada', 'TAVG')
    plot_single_country_var('France', 'TMAX')
    plot_single_country_var('Mexico', 'HUMID')
    plot_single_country_var('United Kingdom', 'PRCP')
    plot_single_country_var('United States', 'HETSTRS')


def compare_countries():
    '''Compare countries for different climate metrics over time.'''
    plot_country_comparisons(
        "TMIN",
        aggregation='min',
        countries=[
            'Afghanistan',
            'Barbados',
            'Cuba',
            'Ethiopia',
            'Hong Kong',
            'United States',
            'Vietnam',
        ]
    )
    plot_country_comparisons(
        "TAVG",
        aggregation='mean',
        countries=[
            'Denmark',
            'France',
            'Greece',
            'Israel',
            'Japan',
            'Kenya',
            'United States',
        ]
    )
    plot_country_comparisons(
        "TMAX",
        aggregation='max',
        countries=[
            'Libya',
            'Morocco',
            'Nepal',
            'Oman',
            'Pakistan',
            'Qatar',
            'United States',
        ]
    )
    plot_country_comparisons(
        "PRCP",
        aggregation='min',
        countries=[
            'Romania',
            'Singapore',
            'Taiwan',
            'United States',
            'Western Sahara',
            'Yemen',
            'Zaire',
        ]
    )
    plot_country_comparisons(
        "HUMID",
        aggregation='mean',
        countries=[
            'Australia',
            'Brazil',
            'China',
            'Djibouti',
            'Ecuador',
            'Fiji',
            'United States',
        ]
    )
    plot_country_comparisons(
        "HETSTRS",
        aggregation='max',
        countries=[
            'Guyana',
            'Haiti',
            'Italy',
            'Jamaica',
            'Kuwait',
            'Laos',
            'United States',
        ]
    )

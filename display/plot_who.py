'''This file includes scripts intended to generate plots for output.

Plotly figures can be saved to JPG interactively through the browser, but saving
them programmatically requires installing an "orca" executable.
'''
import pandas as pd
import plotly.graph_objects as go

from os.path import join
from yaml import safe_load

with open('../files.yaml', 'r') as fp:
    settings = safe_load(fp)

##### utility functions #####

def _get_WHO_population_df():
    processed_dir = settings['who_output_dir']
    population = pd.read_csv(join(processed_dir, 'population.csv'))
    del population['Sex']
    del population['Country']
    return population

##### direct-output data-plot functions #####


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


def plot_WHO_raw_death_bar(years):
    '''Plot death counters with ambiguous labels'''
    raw_mort = pd.read_csv(
        join(settings['who_input_dir'], 'Morticd10_part5.csv')
    )
    raw_mort = raw_mort[['Country', 'Year', 'List', 'Cause', 'Deaths1']]
    names = pd.read_csv(join(settings['who_input_dir'], 'country_codes.csv'))
    df = pd.merge(left=raw_mort, left_on='Country', right=names, right_on='country')
    df = df.rename(columns={'name': 'CountryName'})
    df = df.groupby(['CountryName', 'Year', 'List', 'Cause']).sum().reset_index()
    df['CauseLabel'] = df['List'].map(str) + '-' + df['Cause'].map(str)
    df = df[['CountryName', 'Year', 'CauseLabel', 'Deaths1']][df['Deaths1'] > 0]
    print('There are {} causes and {} countries before merge with population data'.format(
        len(set(df['CauseLabel'])),
        len(set(df['CountryName']))
    ))
    pop = pd.read_csv(join(settings['who_output_dir'], 'population.csv'))
    pop = pop[['CountryName', 'Year', 'Pop1']][pop['Pop1'] > 0]
    pop = pop.groupby(['CountryName', 'Year']).sum()
    full = pd.merge(left=df, on=('CountryName', 'Year'), right=pop)
    full['Mortality'] = full['Deaths1']/full['Pop1']
    full['TextMort'] = full['Deaths1'].map(str) + ' in ' + full['Pop1'].map(str)
    full = full[['CountryName', 'Year', 'Mortality', 'CauseLabel', 'TextMort']][full['Year'].isin(years)]
    print('There are {} causes and {} countries after merge with population data'.format(
        len(set(full['CauseLabel'])),
        len(set(full['CountryName']))
    ))
    go.Figure(
        data=[
            go.Bar(
                name='Mortality due to {}'.format(l, c),
                x=full[full['CauseLabel']==l][full['CountryName']==c]['Year'],
                y=full[full['CauseLabel']==l][full['CountryName']==c]['Mortality'],
                text=full[full['CauseLabel']==l][full['CountryName']==c]['TextMort']
            )
            for l in sorted(set(full['CauseLabel']))[:40] # TODO: limit is arbitrary; find a better limit
            for c in sorted(set(full['CountryName']))
        ],
        layout={
            'title': {'text': 'Mortality in Ukraine for various causes'},
            'hoverlabel': {'namelength': -1},
            'yaxis': {'type': 'log'}
        }
    ).show()


def plot_WHO_mortality_bar(years):
    mort = pd.read_csv(
        join(settings['who_output_dir'], 'Cyprus_mortality.csv')
    )
    mort = mort[mort['DeathsAll']>0][mort['Year'].isin(years)]
    go.Figure(
        data=[
            go.Bar(
                name=set(mort[mort['ListCause']==l][mort['CountryName']==c]['Cause']).pop()[:50],
                x=mort[mort['ListCause']==l][mort['CountryName']==c]['Year'],
                y=mort[mort['ListCause']==l][mort['CountryName']==c]['MortAll'],
                text=mort[mort['ListCause']==l][mort['CountryName']==c]['Cause']
            )
            for l in sorted(set(mort['ListCause']))[:40] # TODO: limit is arbitrary; find a better limit
            for c in sorted(set(full['CountryName']))
        ],
        layout={
            'title': {'text': 'Mortality in Cyprus for various causes'},
            'hoverlabel': {'namelength': -1},
            'yaxis': {'type': 'log'}
        }
    ).show()

##### Script entry point #####

if __name__ == '__main__':
    with open('./files.yaml', 'r') as fp:
        settings = safe_load(fp)

    # Comment out plots which don't need to be regenerated.
    # plot_NOAA_samples()
    # plot_WHO_samples()
    # plot_WHO_raw_death_bar(years=[2018])
    plot_WHO_mortality_bar(years=[2018])
    

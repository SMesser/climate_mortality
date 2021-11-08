'''Calculations connecting the WHO and NOAA data.'''
import pandas as pd

from numpy import array
from os.path import join
from shapefile import Reader
from sys import stdout
from yaml import safe_load

from .annualized import load_annualized_NOAA

with open('./files.yaml', 'r') as fp:
    settings = safe_load(fp)

MODEL_CLIMATE_VARS = [
    # Omit EMNT and EMXT since those have no counterpart in predicted climates.
    "TMIN",
    "TAVG",
    "TMAX",
    "PRCP",
    "HUMID",
    "HETSTRS"
]


def load_country_climate_df():
    '''Load a previously-calculated dataframe for per-country-year climates.'''
    return pd.read_csv(
        join(settings['combined'], 'country_center_climates.csv')
    )


def _get_center_of_shp(shape):
    '''Yield a very hacky approximation to the middle of the shape

    TODO: Do some respectable geometry instead.
    '''
    l = float(len(shape.points))
    x = sum([p[0] for p in shape.points])
    y = sum([p[1] for p in shape.points])
    return (x/l, y/l)


def _get_country_centers():
    '''Return an approximate center for each country based on its perimeter.

    Currently, this average is weighted toward complex coastlines and high
    latitudes because it simply averages the (longitude, latitude) of every
    point _specified_ on the perimeter.

    TODO: Use actual geometry to get a better estimate of the centers, or
    replace this function entirely.
    '''
    source_path = settings['country_shapes']
    reader = Reader(source_path)
    available_country_shapes = [record.NAME for record in reader.records()]
    centers = [_get_center_of_shp(shape) for shape in reader.shapes()]
    records = reader.records()
    center_dict = {
        records[n].NAME: centers[n]
        for n in range(len(records))
    }
    return (
        pd.DataFrame.from_dict([
            {'country': name, 'LONGITUDE': pos[0], 'LATITUDE': pos[1]}
            for name, pos in center_dict.items()
        ]),
        centers
    )


def _spatial_climate_average(raw_df, points):
    '''Spatially average gridded-map dataframe of annualized data.

    Returns a dictionary with the mean of each column. Resolution of the grid
    used in the spatial average matches that of the input raw_df.
    '''
    min_long = min(p[0] for p in points) - 1
    max_long = max(p[0] for p in points) + 1
    min_lat = min(p[1] for p in points) - 1
    max_lat = max(p[1] for p in points) + 1
    return raw_df[
        (min_long <= raw_df['LONGITUDE']) & (raw_df['LONGITUDE'] <= max_long) & (min_lat <= raw_df['LATITUDE']) & (raw_df['LATITUDE'] <= max_lat)
    ].mean().to_dict()


def _load_country_climate(var, year):
    '''Load country-labelled climate data for a particular variable and year.'''
    print(f'Averaging per-country climates for {var} in {year}')
    source_path = settings['country_shapes']
    reader = Reader(source_path)
    names = [record.NAME for record in reader.records()]
    annualized_var = load_annualized_NOAA(var, year)
    climates = [
        _spatial_climate_average(raw_df=annualized_var, points=shape.points)
        for shape in reader.shapes()
    ]
    return pd.DataFrame.from_dict([
        {
            'country': names[n],
            var + '_min': climates[n]['min'],
            var + '_mean': climates[n]['mean'],
            var + '_max': climates[n]['max'],
        }
        for n in range(len(names))
    ])


def _load_climate_year(year):
    '''Load all annualized climate data for one year'''
    print(f'Averaging all climate variables in {year}.')
    stdout.flush()
    interp_vars = sorted(MODEL_CLIMATE_VARS)
    base = _load_country_climate(interp_vars[0], year)
    
    for var in interp_vars[1:]: # 0th var already loaded
        base = pd.merge(
            left=base,
            on='country',
            right=_load_country_climate(var, year)
        )
        
    base['Year'] = year
    return base


def build_composite_climate_df():
    '''Combine the annualized climate data from all vars and countries.'''
    country_climate = pd.concat([
      _load_climate_year(year)
      for year in range(1995, 2021)
    ])
    country_climate.to_csv(
        join(settings['combined'], 'country_center_climates.csv'),
        index=False
    )

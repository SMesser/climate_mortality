'''Calculations connecting the WHO and NOAA data.'''
import pandas as pd

from numpy import array
from shapefile import Reader
from yaml import safe_load

from .annualized import interpolate_annualized_NOAA
from .interpolation import INTERPOLATION_COLUMNS

with open('./files.yaml', 'r') as fp:
    settings = safe_load(fp)


def load_WHO_mortality(country, years):
    mort = pd.read_csv(
        join(settings['who']['output_dir'], f'{country}_mortality.csv')
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
    source_path = settings['country_shapes']
    reader = Reader(source_path)
    available_country_shapes = [record.NAME for record in reader.records()]
    centers = [_get_center_of_shp(shape) for shape in reader.shapes()]
    center_dict = {
        records[n].NAME: centers[n]
        for n in range(len(reader.records()))
    }
    return (
        pd.DataFrame.from_dict([
            {'country': name, 'LONGITUDE': pos[0], 'LATITUDE': pos[1]}
            for name, pos in center_dict.items()
        ]),
        centers
    )


def _load_country_climate(var, year):
    name_df, centers = _get_country_centers()
    # TODO: Instead of return data near middle of each shape, average over the shape.
    climate_df = interpolate_annualized_NOAA(var, year, points=centers)
    merged = pd.merge(
        left=name_df,
        on=('LONGITUDE', 'LATITUDE'),
        right=climate_df
    )
    del merged['LONGITUDE']
    del merged['LATITUDE']
    return merged


def _load_climate_year(year):
    interp_vars = sorted(INTERPOLATION_COLUMNS)
    base = _load_country_climate(interp_vars[0], year)
    for var in interp_vars[1:]: # 0th var already loaded
        base = pd.merge(
            left=base,
            on='country',
            right=_load_country_climate(var, year)
        )


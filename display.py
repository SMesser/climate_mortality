'''This file includes scripts intended to generate plots for output.'''
import pandas as pd
import plotly.graph_objects as go

from os.path import join
from yaml import safe_load


with open('./files.yaml', 'r') as fp:
    settings = safe_load(fp)

# NOAA data
df = pd.read_csv(join(settings['noaa_output_dir'], 'PRCP1995-10.csv'))
fig = go.Figure(data=go.Scattergeo(
    lon=df['LONGITUDE'],
    lat=df['LATITUDE'],
    text=df['PRCP'],
    mode='markers',
    marker_color=df['PRCP']
))

fig.show()


# Script entry point

#if __name__ == '__main__':
#    with open('./files.yaml', 'r') as fp:
#        settings = safe_load(fp)

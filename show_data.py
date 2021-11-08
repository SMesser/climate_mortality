'''This file includes scripts intended to generate plots for output.

Plotly figures can be saved to JPG interactively through the browser, but saving
them programmatically requires installing an "orca" executable.
'''
import pandas as pd
import plotly.graph_objects as go

from os.path import join
from yaml import safe_load

from climate_mortality.display.plot_cmip5 import plot_CMIP5_samples
from climate_mortality.display.plot_noaa import (
    plot_NOAA_annualized,
    plot_NOAA_interp,
    plot_NOAA_samples
)
from climate_mortality.display.plot_who import (
    plot_WHO_mortality_bar, plot_WHO_raw_death_bar,
    plot_WHO_samples
)
from climate_mortality.display.plot_mixed import (
    compare_countries,
    plot_country_var_histories,
)


with open('./files.yaml', 'r') as fp:
    settings = safe_load(fp)

##### Script entry point #####

if __name__ == '__main__':
    with open('./files.yaml', 'r') as fp:
        settings = safe_load(fp)

    # Comment out plots which don't need to be regenerated.
    # plot_NOAA_samples()
    # plot_WHO_samples()
    # plot_WHO_raw_death_bar(years=[2018])
    # plot_WHO_mortality_bar(years=[2018])
    # plot_CMIP5_samples()
    # plot_NOAA_interp()
    # plot_NOAA_annualized()
    plot_country_var_histories()
    compare_countries()

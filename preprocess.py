'''Consolidate data files.'''

from os.path import join
from yaml import safe_load

from climate_mortality.utils.annualized import annualize_all_NOAA
from climate_mortality.utils.ascii_reader import filter_tree
from climate_mortality.utils.noaa_reader import group_NOAA, trim_NOAA
from climate_mortality.utils.interpolation import interpolate_all_NOAA
from climate_mortality.utils.who_reader import (
    convert_country_tables_to_causes,
    process_WHO_dead,
    process_WHO_pop
)
from climate_mortality.utils.connect_noaa_who import (
    build_composite_climate_df,
    join_mortality_climate
)

with open('./files.yaml', 'r') as fp:
    settings = safe_load(fp)


def process_WHO():
    '''Process WHO population & mortality data.'''
    print('\n###########  BEGINNING PROCESSING OF WHO DATA  ############\n')
    
    #process_WHO_pop(
    #    settings['who']['input_dir'],
    #    settings['who']['country_output_dir'],
    #    settings['custom_input_dir']
    #)
    
    #process_WHO_dead(
    #    settings['who']['input_dir'],
    #    settings['who']['country_output_dir'],
    #    settings['custom_input_dir']
    #)

    convert_country_tables_to_causes()


def process_NOAA():
    '''Process NOAA climate observations.'''
    print('\n###########  BEGINNING PROCESSING OF NOAA DATA  ############\n')
    # trim_NOAA(settings['noaa']['input_dir'], settings['noaa']['filtered_dir'])
    # group_NOAA(
    #   settings['noaa']['filtered_dir'],
    #   settings['noaa']['compiled_dir']
    # )
    interpolate_all_NOAA(method='linear')
    annualize_all_NOAA()


def process_CMIP5():
    '''Process CMIP5 climate predictions.'''
    print('\n###########  BEGINNING PROCESSING OF CMIP5 DATA  ############\n')
    filter_tree(skip=1)
        

if __name__ == '__main__':
    # Preprocessing code is retained in case it needs to be run again, and to
    # document the overall process. Eventually, once all preprocessing
    # components are individually & successfully tested & run, this can be
    # re-enabled and the script run as a single piece.
    # TODO: Create command-line parameters to allow piecemeal processing.
    # process_NOAA()
    process_WHO() # This has been completely run once
    # process_CMIP5() # This has been completely run once
    # build_composite_climate_df()
    # join_mortality_climate()
    

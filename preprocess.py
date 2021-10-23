'''Consolidate data files.'''

from os.path import join
from yaml import safe_load

from climate_mortality.utils.ascii_reader import filter_tree
from climate_mortality.utils.noaa_reader import group_NOAA, trim_NOAA
from climate_mortality.utils.interpolation import interpolate_all_NOAA
from climate_mortality.utils.who_reader import process_WHO_dead, process_WHO_pop

with open('./files.yaml', 'r') as fp:
    settings = safe_load(fp)


def process_WHO():
    '''Process WHO population & mortality data.'''
    print('\n###########  BEGINNING PROCESSING OF WHO DATA  ############\n')
    
    process_WHO_pop(
        settings['who_input_dir'],
        settings['who_output_dir'],
        settings['custom_input_dir']
    )
    
    process_WHO_dead(
        settings['who_input_dir'],
        settings['who_output_dir'],
        settings['custom_input_dir']
    )


def process_NOAA():
    '''Process NOAA climate observations.'''
    print('\n###########  BEGINNING PROCESSING OF NOAA DATA  ############\n')
    # trim_NOAA(settings['noaa_input_dir'], settings['noaa_filtered_dir'])
    # group_NOAA(settings['noaa_filtered_dir'], settings['noaa_compiled_dir'])
    interpolate_all_NOAA(
        settings['noaa_compiled_dir'],
        settings['noaa_interpolated_dir']
    )


def process CMIP5():
    '''Process CMIP5 climate predictions.'''
    print('\n###########  BEGINNING PROCESSING OF CMIP5 DATA  ############\n')
    filter_tree(skip=4)
        

if __name__ == '__main__':
    # Preprocessing code is retained in case it needs to be run again, and to
    # document the overall process. Eventually, once all preprocessing
    # components are individually & successfully tested & run, this can be
    # re-enabled and the script run as a single piece.
    # TODO: Create command-line parameters to allow piecemeal processing.
    process_NOAA()
    # process_WHO() # This has been completely run once
    # process_CMIP5() # This has been completely run once

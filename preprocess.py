'''Consolidate data files.'''

from os.path import join
from yaml import safe_load

from utils.ascii_reader import filter_tree
from utils.noaa_reader import group_NOAA, trim_NOAA
from utils.who_reader import process_WHO_dead, process_WHO_pop


if __name__ == '__main__':
    with open('./files.yaml', 'r') as fp:
        settings = safe_load(fp)

    '''
    # Preprocessing code is retained in case it needs to be run again, and to
    # document the overall process. Eventually, once all preprocessing
    # components are individually & successfully tested & run, this can be
    # re-enabled and the script run as a single piece.

    print('\n###########  BEGINNING PROCESSING OF NOAA DATA  ############\n')
    
    # NOAA GSOM data has been trimmed once. 
    trim_NOAA(settings['noaa_input_dir'], settings['noaa_filtered_dir'])
    group_NOAA(settings['noaa_filtered_dir'], settings['noaa_output_dir'])

    print('\n###########  BEGINNING PROCESSING OF WHO DATA  ############\n')
    
    # WHO population & mortality has been processed once.
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
    '''
    print('\n###########  BEGINNING PROCESSING OF CMIP5 DATA  ############\n')
    
    filter_tree(skip=4)

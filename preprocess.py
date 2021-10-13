'''Consolidate data files.'''

from yaml import safe_load

from utils.noaa_reader import group_NOAA, trim_NOAA
from utils.who_reader import process_WHO


if __name__ == '__main__':
    with open('./files.yaml', 'r') as fp:
        settings = safe_load(fp)

    # NOAA GSOM data has been trimmed once. Code is retained in
    # case it needs to be run again, and to document the overall process.
    # trim_NOAA(settings['noaa_input_dir'], settings['noaa_filtered_dir'])
    # group_NOAA(settings['noaa_filtered_dir'], settings['noaa_output_dir'])
    
    # WHO population has been trimmed once.
    #process_WHO_pop(
    #    settings['who_input_dir'],
    #    settings['who_output_dir'],
    #    settings['custom_input_dir']
    #)

    process_WHO_dead(
        settings['who_input_dir'],
        settings['who_output_dir'],
        settings['custom_input_dir']
    )

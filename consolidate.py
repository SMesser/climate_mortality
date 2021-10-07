'''Consolidate data files.'''

from yaml import safe_load

from utils.noaa_reader import trim_noaa


if __name__ == '__main__':
    with open('./files.yaml', 'r') as fp:
        settings = safe_load(fp)

    # NOAA GSOM data has been trimmed once. Code is retained in
    # case it needs to be run again, and to document the overall process.
    # trim_noaa(settings['noaa_input_dir'], settings['noaa_output_dir'])

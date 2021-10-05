'''Consolidate data files.'''

from os import getcwd, listdir
from os.path import join

from pprint import pformat

from utils.noaa_reader import DATA_COLUMNS, trim_file


def trim_noaa(source_dir, dest_dir):
    '''Loop over all NOAA files, trimming target period & variables.

    e.g. '/Users/Sarah/Documents/UMUC/DATA 670/datasets/NOAA GSOM Current Climate/'
    fn = 'C:\\Users\\Sarah\\Documents\\UMUC\\DATA 670\\datasets\\NOAA GSOM Current Climate\\'
    listdir(fn)
    '''
    file_count = 0
    record_count = 0
    counts = {field: 0 for field in DATA_COLUMNS}
    
    for filename in listdir(source_dir):
        source_path = join(source_dir, filename)
        dest_path = join(dest_dir, filename)

        if filename.endswith('.csv'):
            print(f'Trimming {filename}')
            rows, columns = trim_file(source_path, dest_path, '1995-01')

            for col in columns:
                counts[col] += rows
            
            if rows:
                file_count += 1
                record_count += rows
        else:
            print(f'Skipping {filename}.')

    print(f'Wrote {record_count} rows across {file_count} files.')
    print(
        f'These are the counts by data column: {pformat(counts)}'
    )    

if __name__ == '__main__':
    from yaml import safe_load
    with open('./files.yaml', 'r') as fp:
        settings = safe_load(fp)

    trim_noaa(settings['noaa_input_dir'], settings['noaa_output_dir'])

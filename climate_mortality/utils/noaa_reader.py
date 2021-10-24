'''This file contains read/write utilities for reading and filtering NOAA CSV.

The functions in this file can read CSV files like those in the NOAA GSOM data
set.

Output format is CSV, and can be filtered during read.

TODO:
* Interpolate across the spatially-uneven samples to get a map per variable,
per month.
* Using the interpolated GSOM data, create new maps with the annualized lowest,
highest, and mean temperatures & precipitation for each location. Also create an
annualized (low, mean, high) map for temperature * precipitation as a proxy for
absolute humidity.
* Spatially average the annualized maps across each country to estimate climate
via (low, avg, high) values for precipitation and temperature. 
'''
import pandas as pd

from csv import DictReader, DictWriter

from os import listdir, remove
from os.path import join

from pprint import pformat
from sys import stdout
from yaml import safe_load

# Lower-level / independent functions are near the top.
# Functions which depend on them are further down.
# Classes are at the bottom.

ID_COLUMNS = {
    "STATION",
    "DATE",
    "LATITUDE",
    "LONGITUDE",
}


# "<*>_ATTRIBUTES" columns describe dates of extremes, source of data, and
# missing data. They have roughly the same format for the GSOM and GSOY
# datasets.
DATA_COLUMNS = {
    "EMNT",  # Extreme minimum temperature
#    "EMNT_ATTRIBUTES",
    "PRCP",  # Total precipitation for the period
#    "PRCP_ATTRIBUTES",
    "TAVG",  # Average temperature
#    "TAVG_ATTRIBUTES",
    "EMXT",  # Extreme maximum temperature
#    "EMXT_ATTRIBUTES",
    "TMAX",  # Average maximum temperature
#    "TMAX_ATTRIBUTES",
    "TMIN",  # Average minimum temperature
#    "TMIN_ATTRIBUTES",
}

with open('./files.yaml', 'r') as fp:
    settings = safe_load(fp)

# Functions with only external dependencies

def read_source_header(source_file, id_fields, data_fields):
    '''Confirm there is data to read from the input CSV.'''
    source = DictReader(source_file)
    source_fields = source.fieldnames
    missing_id_fields = id_fields - set(source_fields)
    
    if missing_id_fields:
        raise ValueError(
            f'Source CSV file {source_file.name} is missing required id fields {missing_id_fields}'
        )

    filtered_data_fields = set(source_fields) & data_fields
    return source, filtered_data_fields


def _to_be_written(var, source_row, date_str):
    '''Return True iff this row should be written out.'''
    if not (var in source_row):
        return False
    if source_row[var]=='':
        return False
    return (source_row['DATE']==date_str)


def load_compiled_NOAA(var, year, month):
    '''Load NOAA data for a single variable in a given month.'''
    return pd.read_csv(
        join(settings['noaa']['compiled_dir'], f'{var}{year}-{month}.csv')
    )

# Functions with internal dependencies

def _trim_open_csv(
    source_file,
    output_name,
    min_date,
    id_fields=None,
    data_fields=None
):
    '''Filter a CSV file to a smaller output target, by date and by data fields.'''
    source, avail_data = read_source_header(
        source_file,
        id_fields,
        data_fields
    )

    if not avail_data:
        print(
            f'None of desired data fields {data_fields} are present. Skipping write of empty file.'
        )
        return 0, []

    all_fields = set(id_fields) | avail_data

    with open(output_name, 'w') as dest_file:
        destination = DictWriter(dest_file, fieldnames=all_fields, dialect='unix')
        destination.writeheader()
        written = 0
        
        for source_row in source:
            if source_row['DATE'] >= min_date:
                written += 1
                dest_row = {
                    key: value
                    for key, value in source_row.items()
                    if key in all_fields
                }
                destination.writerow(dest_row)

    if not written:
        print(f'Skipping since it has no data since before {min_date}.')
        try:
            remove(output_name)
        except FileNotFoundError:
            # If the file's already gone, that's good.
            pass

    return written, avail_data


def trim_file(
    input_name,
    output_name,
    min_date,
    id_fields=None,
    data_fields=None
):
    '''Filter a CSV file to a smaller output target, by date and by data fields.

    Records which are missing any of the id_fields are omitted.
    Output files will have the intersection of the given data_fields with the
    fields listed in the file header.

    If id_fields is None (the default), ID_COLUMNS is used instead.
    if data_fields is None (the default), DATA_COLUMNS is used instead.
    '''
    
    if id_fields is None:
        id_fields = ID_COLUMNS
    else:
        id_fields = set(id_fields)

    if data_fields is None:
        data_fields = DATA_COLUMNS
    else:
        data_fields = set(data_fields)

    with open(input_name, 'r') as source_file:
        return _trim_open_csv(
            source_file,
            output_name,
            min_date,
            id_fields,
            data_fields
        )


def trim_NOAA(source_dir, dest_dir):
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


def _print_group_update(full_in_files, used_in_files, in_records):
   print(
       'Processed {} files, {} of which have been useful, for {} records'.format(
           full_in_files,
           used_in_files,
           in_records
        )
    ) 


def _make_one_group(source_dir, dest_dir, var, year, month, source_list):
    '''Write a single one of the regrouped output files.'''
    out_cols = ['LONGITUDE', 'LATITUDE', var]
    date_str = f'{year}-{month:02}'
    dest_name = join(dest_dir, f'{var}{year}-{month}.csv')
    print(f'Writing to {dest_name}')
    stdout.flush()
    full_in_files = 0
    used_in_files = 0
    out_records = 0

    with open(dest_name, 'w') as dest_fp:
        writer = DictWriter(dest_fp, fieldnames=out_cols, dialect='unix')
        writer.writeheader()
                    
        for source_name in source_list:
            full_in_files += 1
            
            with open(join(source_dir, source_name), 'r') as source_fp:
                reader_dict = DictReader(source_fp)
                used_this = False

                for source_row in reader_dict:
                    if _to_be_written(var, source_row, date_str):
                        used_this = True
                        out_records += 1
                        writer.writerow({
                            col: source_row[col]
                            for col in out_cols
                        })

                if used_this:
                    used_in_files += 1
            
            if full_in_files % 10000 == 0:
                _print_group_update(full_in_files, used_in_files, out_records)

    _print_group_update(full_in_files, used_in_files, out_records)
    
    if not out_records:
        remove(dest_name)


def group_NOAA(source_dir, dest_dir):
    '''Group all NOAA observations into separate files by month and variable.'''
    source_list = listdir(source_dir)
    
    for year in range(1995, 2022):
        for month in range(1, 13):
            for var in DATA_COLUMNS:
                _make_one_group(
                    source_dir,
                    dest_dir,
                    var,
                    year,
                    month,
                    source_list
                )

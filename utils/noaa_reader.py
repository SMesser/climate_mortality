'''This file contains read/write utilities for reading and filtering NOAA CSV.

The functions in this file can read CSV files like those in the NOAA GSOM data
set.

Output format is CSV, and can be filtered during read.
'''

from csv import DictReader, DictWriter
from os import remove

# Lower-level / independent functions are near the top.
# Functions which depend on them are further down.
# Classes are at the bottom.

ID_COLUMNS = {
    "STATION",
    "DATE",
    "LATITUDE",
    "LONGITUDE",
}

DATA_COLUMNS = {
    "EMNT",
    "EMNT_ATTRIBUTES",
    "PRCP",
    "PRCP_ATTRIBUTES",
    "TAVG",
    "TAVG_ATTRIBUTES",
    "TMAX",
    "TMAX_ATTRIBUTES",
    "TMIN",
    "TMIN_ATTRIBUTES",
}

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
        destination = DictWriter(dest_file, fieldnames=all_fields)
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

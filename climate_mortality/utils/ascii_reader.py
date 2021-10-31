'''This file contains read/write utilities for transforming GIS files to CSV.

The functions in this file can read ASCII GIS files like those from the
CCAFS-CMIP5 group climate projections

Output format is CSV, and can be filtered during read.
'''

import sys

from math import ceil, floor

from os import listdir, mkdir
from os.path import isdir, join

from string import whitespace
from sys import stdout
from yaml import safe_load

# Lower-level / independent functions are near the top.
# Functions which depend on them are further down.
# Classes are at the bottom.

FILE2VAR = {
    'prec': 'PRCP',
    'tmax': 'TMAX',
    'tmean': 'TAVG',
    'tmin': 'TMIN',
}


DIMENSION_LOOKUP = {
    'prcp': 'mm',
    'tmin': 'Celsius',
    'tavg': 'Celsius',
    'tmax': 'Celsius',
    'value': 'unknown'
}

# Scale from
# https://cgspace.cgiar.org/bitstream/handle/10568/90730/abbreviations_used_in_ccafs_climate.pdf?sequence=1&isAllowed=y
SCALE_LOOKUP = {
    'prcp': 1.0,
    'tmin': 0.1,
    'tavg': 0.1,
    'tmax': 0.1,
    'value': 1.0
}


with open('./files.yaml', 'r') as fp:
    settings = safe_load(fp)


# Functions with only external dependencies

def read_token(fp):
    '''Read a single whitespace-delimited token from the file.

    Leading whitespace is ignored. File pointer fp will be at the second
    character after the end of the token.
    '''
    # Skip any initial whitespace
    c = fp.read(1)
    
    while c and (c in whitespace):
        c = fp.read(1)

    # extract the token
    token = ''
    
    while c and (c not in whitespace):
        token = token + c
        c = fp.read(1)

    return token

    
def skip_this_ndx(xn, yn, xskip, yskip):
    '''Return True iff indices (xn, yn) indicate this item should be skipped.'''
    return  ((xn % (xskip + 1) > 0) or (yn % (yskip + 1)) > 0)


def skip_this_pos(xpos, ypos, xmin=-180, xmax=180, ymin=-90, ymax=90):
    '''Return True iff position indicates this item should be skipped.

    Defaults assume x and y refer to longitude and latitude, respectively
    '''
    return  (xpos < xmin) or (xpos > xmax) or (ypos < ymin) or (ypos > ymax)

# Functions with internal dependencies

def check_bounds(value, dimension='Celsius'):
    '''Determines whether the given value is unrealistic for is dimension.'''
    if dimension == 'Celsius':
        if -95.0 <= value <= 65.0:
            return True
    elif dimension == 'mm':
        if 0.0 <= value <= 30000:
            return True
    raise DataOutOfBoundsError(f'Found unrealistic value {value} for dimension {dimension}.')
    

def asc_to_array(
    filepath,
    xskip=0,
    yskip=0,
    xmin=-180,
    xmax=180,
    ymin=-90,
    ymax=90,
    dimension='Celsius',
    scale=1.0
):
    '''This function downsamples a GIS ASCII file into a Python array of tuples.

    Inputs:
        filepath    path of the ASCII file source.
        xskip=0     number of x columns to skip between retained values
        yskip=0     number of y rows to skip between retained values

    Note that \n characters in the target file are *NOT* guaranteed to be at the
    logical line ends.  The total number of items in the file is fixed, though,
    so we specifically track the logical row & column.

    Compare
    http://surferhelp.goldensoftware.com/subsys/subsys_ASC_Arc_Info_ASCII_Grid.htm
    https://desktop.arcgis.com/en/arcmap/latest/manage-data/raster-and-images/esri-ascii-raster-format.htm
    '''
    data_array = []
    
    with open(filepath, 'r') as asc:
        fmt = ASCIIFormat(asc)
        xn = 0
        yn = 0
        item_str = read_token(asc)
        total = 0
        
        while item_str:
            total += 1
            if item_str != fmt.null:
                xpos = fmt.xllcorner + xn * fmt.cellsize
                ypos = fmt.yllcorner + (fmt.nrows - yn) * fmt.cellsize
                
                if not (skip_this_ndx(xn, yn, xskip, yskip) or skip_this_pos(xpos, ypos, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)):
                    val = float(item_str) * scale
                    check_bounds(val, dimension=dimension)
                    data_array.append((xpos, ypos, val))
                    if len(data_array) % 100000 == 0:
                        print(
                            'Reading {} in progress.  {} non-null values read so far.'.format(
                                filepath,
                                len(data_array)
                            )
                        )
                        sys.stdout.flush()

            xn += 1
            item_str = read_token(asc)
            
            if xn == fmt.ncols:
                xn = 0
                yn += 1

    print('Read {} total, and {} non-null values.'.format(total, len(data_array)))
    return data_array


def asc_to_filtered_csv(
    infile,
    outfile,
    xskip=0,
    yskip=0,
    label='value',
    xmin=-180,
    xmax=180,
    ymin=-90,
    ymax=90
):
    '''This function downsamples a GIS ASCII file into a CSV format.

    Inputs:
        infile      path of the ASCII file source
        outfile     path of the CSV file destination
        xskip=0     number of x columns to skip between retained values
        yskip=0     number of y rows to skip between retained values
        label="value" name of the "value" column in the output CSV
        xmin=-180   minimum x position
        xmax=180    maximum x position
        ymin=-90    minimum y position
        ymax=90     maximum y position
    '''

    try:
        arr = asc_to_array(
            infile,
            xskip=xskip,
            yskip=yskip,
            xmin=xmin,
            xmax=xmax,
            ymin=ymin,
            ymax=ymax,
            dimension=DIMENSION_LOOKUP[label.lower()],
            scale=SCALE_LOOKUP[label.lower()],
        )
    except DataOutOfBoundsError as exc:
        print(f'Skipping output from {infile}: {exc}')
    else: 
        with open(outfile, 'w') as outf:
            outf.write('LONGITUDE,LATITUDE,{}\n'.format(label))
            for ln in arr:
                outf.write('{}, {}, {}\n'.format(ln[0], ln[1], ln[2]))


def filter_asc_dir(
    source_dir,
    dest_dir,
    xskip=0,
    yskip=0,
    label=None,
    xmin=-180,
    xmax=180,
    ymin=-90,
    ymax=90
):
    '''Process all ASC files in the source directory.

    Inputs:
        source_dir   directory of the ASCII file source
        dest_dir     directory of the CSV file destination
        xskip=0     number of x columns to skip between retained values
        yskip=0     number of y rows to skip between retained values
        label="value" name of the "value" column in the output CSV
        xmin=-180   minimum x position
        xmax=180    maximum x position
        ymin=-90    minimum y position
        ymax=90     maximum y position
    '''
    
    for fname in listdir(source_dir):
        if fname.endswith('.asc'):
            source_fn = join(source_dir, fname)
            name_parts = fname.split('.')
            name_parts[-1] = 'csv'
            dest_name = '.'.join(name_parts)
            dest_fn = join(dest_dir, dest_name)
            
            if label is None:
                this_label = FILE2VAR[name_parts[0].split('_')[0]]
            else:
                this_label = label
    
            print(f'Processing {source_fn} -> {dest_fn} for {this_label}')
            asc_to_filtered_csv(
                source_fn,
                dest_fn,
                xskip=xskip,
                yskip=yskip,
                label=this_label,
                xmin=xmin,
                xmax=xmax,
                ymin=ymin,
                ymax=ymax
            )
            stdout.flush()

def filter_tree(skip=0):
    source_dir = settings['cmip5']['input_dir']
    dest_dir = settings['cmip5']['output_dir']
    
    for datadir in listdir(source_dir):
        in_dir = join(source_dir, datadir)
        if isdir(in_dir):
            print(f'Processing {datadir}')
            out_dir = join(dest_dir, datadir)
            try:
                mkdir(out_dir)
            except FileExistsError:
                pass # Just need to make sure it's here; don't need to empty it.

            filter_asc_dir(
                in_dir,
                out_dir,
                xskip=skip,
                yskip=skip,
                xmin=-125,
                xmax=-65,
                ymin=24,
                ymax=50
            )

# Classes

class DataOutOfBoundsError(ValueError):
    pass


class ASCIIFormat(object):
    '''This class encapsulates format information for an ASCII file.'''
    def __init__(self, fp):
        '''Initialize with a file pointer to the file which should be read.

        The file pointer, fp, should be positioned at the beginning of a file
        which is already opened for reading.
        When __init__ exits, fp is positioned at the first data value, after the
        header block.
        '''
        fp.seek(0)
        self.ncols = self._read_header_val(fp, 'ncols', int)
        self.nrows = self._read_header_val(fp, 'nrows', int)
        self.xllcorner = self._read_header_val(fp, 'xllcorner', float)
        self.yllcorner = self._read_header_val(fp, 'yllcorner', float)
        self.cellsize = self._read_header_val(fp, 'cellsize', float)
        self.null = self._read_header_val(fp, 'NODATA_value', str)

    def _read_header_val(self, fp, prefix, fmt):
        '''Read a one-line header string and return the corresponding value.'''
        ln = fp.readline()

        if not ln:
            raise ValueError('Missing expected header data {}.'.format(prefix))

        label, value = ln.split()

        if label.lower() != prefix.lower():
            raise ValueError(
                'Found label {} when expecting label {}'.format(label, prefix)
            )
        
        return fmt(value)


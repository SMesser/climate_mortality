'''This file contains read/write utilities for reading WHO ICD-10 mortality CSV.

TODO:
* Drop IM mortality data after confirming the entries are either all blank or
sum to the lowest regular age bracket's deaths (0-1 y.o.).
* Treat all blanks as zeroes.
* After ingestion, check the sum across all age groups matches the count in the
"all ages" column. Reject any rows that do not match, unless the all-ages column
was blank.
* Drop rows for which I cannot find a SHP boundary record.
'''

from pandas import DataFrame

from csv import DictReader, DictWriter
from os import remove


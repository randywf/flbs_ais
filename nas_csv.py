#!/usr/bin/env python3

"""
Use this script to remove unwanted columns from a csv file. Outputs the result
csv file to <original filename>_modified.csv
Usage: nas_csv.py <csv_file> <"comma","separated","columns","to","keep">
"""

import csv
import sys

# NOTE: Use pandas instead?
#from pandas import read_csv

# TODO: Add method for using this module in other files

if __name__ == "__main__":
    args = sys.argv
    filename = sys.argv[1][:sys.argv[1].rfind('.')]
    request_columns = sys.argv[2].split(',')
    request_columns_num = []
    # TODO: Add error checking for input

    with open(args[1]) as csv_in:
        # NOTE: Would dictreader/writer be a better choice?
        csv_reader = csv.reader(csv_in, delimiter = ',')
        column_names = csv_reader.__next__()

        column_number = 0
        for column in column_names:
            for request_column in request_columns:
                if request_column == column:
                    request_columns_num.append(column_number)
            column_number += 1
        
        with open(f"{filename}_modified.csv", 'w') as csv_out:
            csv_writer = csv.writer(csv_out, delimiter = ',')
            for row in csv_reader:
                new_row = []
                for num in request_columns_num:
                    new_row.append(row[num])
                csv_writer.writerow(new_row)

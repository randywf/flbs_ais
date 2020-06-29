#!/usr/bin/env python3

"""
Use this script to remove unwanted columns from a csv file. Outputs the result
csv file to <original filename>_modified.csv
Usage: nas_csv.py <csv_file> <"comma","separated","columns","to","keep">
"""

import sys
import pandas as pd
import numpy as np


def process_csv_df(csv_file, keep_columns):
    df = pd.read_csv(csv_file, low_memory=False)
    column_names = df.columns
    drop_columns = np.setdiff1d(column_names, keep_columns)

    df = df.drop(drop_columns, axis=1)
    df = df.rename(columns={'Specimen Number':'key',
                            'Latitude':'latitude',
                            'Longitude':'longitude'})
    df = df.set_index('key')
    df = df.dropna()
    
    return df


if __name__ == "__main__":
    filename = sys.argv[1][:sys.argv[1].rfind('.')]
    new_filename = f"{filename}_modified.csv"
    keep_columns = sys.argv[2].split(',')
    test_df = process_csv_df(sys.argv[1], keep_columns)
    test_df.to_csv(new_filename)

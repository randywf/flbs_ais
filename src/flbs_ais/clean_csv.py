#!/usr/bin/env python3

import numpy as np
import pandas as pd


def _rename_year(df):
    if 'system:index' in df:
        # Remove after character 10 to remove uniqueness
        df['system:index'] = df['system:index'].map(lambda x: str(x)[:10])
        uniques = df['system:index'].unique()
        years = list(range(2002,2014)) + list(range(2015,2017))
        dates = {u : y for (u,y) in zip(uniques,years)}
        df['system:index'] = df['system:index'].replace(dates)
    return df


def _manage_columns(df, drop_list, name_dict):
    for colname in drop_list:
        if colname not in df:
            raise ValueError(f"Can't drop column '{colname}' - '{colname}' does not exist in dataframe")
    for colname in list(name_dict.keys()):
        if colname not in df:
            raise ValueError(f"Can't rename '{colname}' to '{name_dict[colname]}' - '{colname}' does not exist in dataframe")
        if colname in drop_list:
            raise ValueError(f"Can't rename '{colname}' to '{name_dict[colname]}' - '{colname}' in drop_list")
    df = df.drop(drop_list, axis=1)
    df = df.rename(columns=name_dict)
    return df


def clean_csv(filename, output='df', drop_columns=[], keep_columns=[], split_columns=[], rename_columns={}, rename_year=True):
    df_dict = {}
    drop_list = []
    filename_left = filename[:filename.rfind('.')]
    csv_df = pd.read_csv(filename)

    if output not in ['csv', 'df']:
        raise ValueError(f"Output value '{output}' is invalid - Options are 'csv' and 'df'")

    if drop_columns and keep_columns:
        if list(csv_df.columns) != drop_columns + keep_columns:
            drop_list = drop_columns
        else:
            raise ValueError(f"Drop column list and keep column list do not combine to make set of all columns")
    elif drop_columns:
        drop_list = drop_columns
    elif keep_columns:
        drop_list = np.setdiff1d(list(csv_df.columns), keep_columns)
    
    # Renaming: Check if keeping a renamed column
    for column in keep_columns:
        for item in list(rename_columns.items()):
            if column == item[1]:
                drop_list = np.delete(drop_list, np.where(drop_list == item[0]))

    if rename_year:
        csv_df = _rename_year(csv_df)

    csv_df = _manage_columns(csv_df, drop_list, rename_columns)

    if split_columns:
        for column in split_columns:
            if column in df_out:
                # using renamed column
                df_out = csv_df.drop(column, axis=1)
            elif column in list(rename_columns.keys()):
                # using original column
                df_out = csv_df.drop(rename_columns[column], axis=1)
            else:
                raise ValueError(f"Can't split dataframe by column '{column}' - Does not exist in dataframe")
            df_dict[f"{filename_left}_{column}.csv"] = df_out
    else:
        df_dict[f"{filename_left}_clean.csv"] = csv_df
    
    if output == 'csv':
        for key in list(df_dict.keys()):
            df_dict[key].to_csv(key, index=False)
    else:
        return df_dict

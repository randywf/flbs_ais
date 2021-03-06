#!/usr/bin/env python3
import sys

import pandas as pd
import numpy as np

##from flbs_ais.drop_collinear import drop_collinear
from sklearn.model_selection import train_test_split
from rfpimp import feature_dependence_matrix



def _get_partial_dependencies(X, y, threshold, test_size=0.2, random_state=1):
    X_train = train_test_split(X, y, test_size=test_size, random_state=random_state)[0]
    df = feature_dependence_matrix(X_train)

    # Drop dependence column
    df = df.drop(columns='Dependence')

    # Replace self relationships with NaN
    df = df.mask(df == 1)

    # Mask all cells less than threshold
    df = df.mask(df < threshold)

    # Melt table to get relationships of each row to each column in pairs
    df = df.reset_index().melt(id_vars='index')

    # Take advantage of fact that NaN != NaN to find non-NaN values in table
    df = df.query('value == value')

    # Drop rows that are reverse duplicates of other rows
    if not df.empty:
        check_string_list = []
        for row in df.itertuples():
            string = ''.join(sorted([row[1], row[2]]))
            check_string_list.append(string)
        df.insert(3, "check_string", check_string_list)
        df = df.drop_duplicates('check_string')
        df = df.drop('check_string', axis=1)
    
    return df


def _get_input_drop(value):
    while True:
        choice = input(f"Drop '{value[0]}' {''.ljust(28-len(value[0]))} or '{value[1]}'? {''.ljust(28-len(value[1]))} Dependence: {value[2]:.2f} (1/2/n): ")
        if choice not in ('1','2','n'):
            print(f"Entered: {choice}, try entering 1, 2, or n")
        else:
            break
    if choice == '1': choice = 0
    if choice == '2': choice = 1
    if choice == 'n': choice = None
    return choice


def remove_partial_dependencies(X, y, threshold, interactive=True, verbose=False, dropped_list=None):
    # Get partial dependencies
    if verbose:
        print("Building partial dependency table...")
    df_partial = _get_partial_dependencies(X, y, threshold)    
    
    # Base case: No partial dependencies above the threshold
    if df_partial.empty:
        if verbose:
            print("Done.")
        return X
    
    # Recursive: Drop partial dependencies and run again
    if interactive:
        drop_cols = []
        values = df_partial.values
        if verbose:
            for value in values:
                print(f"'{value[0]}'{''.ljust(28-len(value[0]))} {value[2]:.2f} dependence with: \t'{value[1]}'")
        for value in values:
            choice = _get_input_drop(value)
            if choice is not None:
                drop_cols.append(value[choice])
    else:
        drop_cols = list(df_partial['index'].values)
    
    # Remove duplicate columns from drop_cols
    drop_cols = list(dict.fromkeys(drop_cols))
    
    if verbose:
        print("Dropping: ", end='')
        for i, drop_col in enumerate(drop_cols):
            if i: print(', ', end='')
            print(drop_col, end='')
        print()
    
    # Check if dropped_list was passed as a parameter (dropped_list will not be default value)
    # This is necessary because checking if None evaluates True in the case of both the default
    # argument and in the case of an empty list that was passed as the parameter 'dropped_list'
    if dropped_list is not remove_partial_dependencies.__defaults__[2]:
        # Append() will modify the list that was passed as the parameter, not a copy
        for drop_col in drop_cols:
            dropped_list.append(drop_col)

    X = X.drop(columns=drop_cols, axis=1)

    if interactive:
        choice = -1
        while True:
            choice = input("Continue finding partial dependencies? (y/n): ")
            if choice in ('y', 'n'):
                break
        if choice == 'y':
            return remove_partial_dependencies(X, y, threshold, verbose=verbose, dropped_list=dropped_list)
        else:
            return X
    else:
        return remove_partial_dependencies(X, y, threshold, verbose=verbose, dropped_list=dropped_list)

"""
if __name__ == "__main__":        
    csv_WCT = pd.read_csv("../../tmp/WCT_Clean.csv")
    csv_RBT = pd.read_csv("../../tmp/RBT_Clean.csv")

    X_wct = csv_WCT.drop(['weightedPWCT','Percent_NonTree_Vegetation',
                        'Percent_NonVegetated','fall_totalPrecip','Cloud','huc12'], axis=1)

    y_wct = csv_WCT['weightedPWCT']
    X_rbt = csv_RBT.drop(['weightedPRBT','Percent_NonTree_Vegetation',
                        'Percent_NonVegetated','fall_totalPrecip','Cloud','huc12'],axis=1)
    y_rbt = csv_RBT['weightedPRBT']

    X_wct_collinear = drop_collinear(X_wct,0.7)
    X_rbt_collinear = drop_collinear(X_rbt,0.7)

    _get_partial_dependencies(X_wct_collinear, y_wct, 0.6)
"""

#!/usr/bin/env python3
import sys

import pandas as pd
import numpy as np

from flbs_ais.drop_collinear import drop_collinear
from sklearn.model_selection import train_test_split
from rfpimp import feature_dependence_matrix



def get_partial_dependencies(X, y, threshold, test_size=0.2, random_state=1):
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
    df['check_string'] = df.apply(lambda row: ''.join(sorted([row['index'], row['variable']])), axis=1)
    df = df.drop_duplicates('check_string')
    df = df.drop('check_string', axis=1)
    
    return df


def get_input_drop(value):
    choice = -1
    while True:
        choice = eval(input(f"Drop '{value[0]}' {''.ljust(28-len(value[0]))} or '{value[1]}'? {''.ljust(28-len(value[1]))} Dependence: {value[2]:.2f} (1/2/n): "))
        if choice not in (1, 2, 'n'):
            print(f"Entered: {choice}, try entering 1, 2, or n")
        else:
            break
    if choice == 1:   choice = 0
    if choice == 2:   choice = 1
    if choice == 'n': choice = None
    return choice


def remove_partial_dependencies(X, y, threshold, interactive=True, verbose=False):
    # Get partial dependencies
    if verbose:
        print("Building partial dependency table...")
    df_partial = get_partial_dependencies(X, y, threshold)    
    
    # Base case: No partial dependencies above the threshold
    if df_partial.empty:
        if verbose:
            print("Done.")
        return X
    
    # Recursive: Drop partial depencies and run again
    if interactive:
        drop_cols = []
        values = df_partial.values
        for value in values:
            choice = get_input_drop(value)
            if choice:
                drop_cols.append(value[choice])
    else:
        drop_cols = list(df_partial['index'].values)
    
    if verbose:
        print("Dropping: ", end='')
        for i, drop_col in enumerate(drop_cols):
            if i: print(', ', end='')
            print(drop_col, end='')
        print()
    
    X = X.drop(columns=drop_cols, axis=1)
    return remove_partial_dependencies(X, y, threshold, verbose=verbose)


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

    get_partial_dependencies(X_wct_collinear, y_wct, 0.6)

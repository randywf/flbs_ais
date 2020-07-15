#!/usr/bin/env python3

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
    
    return df


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

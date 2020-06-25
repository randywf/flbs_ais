#!/usr/bin/env python3

"""
Given a species ID, this script returns all occurrences of this species from
the NAS database and puts the results into a csv file. By default it will only
keep key, latitude, and longitude columns
Usage: occurrence.py <species_id> <api_key>
"""

import requests
import sys
import numpy as np
import pandas as pd


def getdf(species_id, columns=None, limit=100, api_key=None):
    url_base = 'http://nas.er.usgs.gov/api/v1/'

    if columns is not None:
        keep_columns = columns
    else:
        keep_columns = ['key','decimalLatitude','decimalLongitude']

    if api_key is not None:
        url_request = f"{url_base}/occurrence/search?species_ID={species_id}&api_key={api_key}"
    else:
        url_request = f"{url_base}/occurrence/search?species_ID={species_id}"
    
    request_json = requests.get(url_request, params={'limit':limit}).json()
    
    column_names = list(request_json['results'][0].keys())
    drop_columns = np.setdiff1d(column_names, keep_columns)
    
    request_df = pd.json_normalize(request_json, 'results')
    request_df = request_df.drop(drop_columns, axis=1)
    request_df = request_df.set_index('key')
    
    return request_df


if __name__ == "__main__":
    try:
        input_species_id = sys.argv[1]
        api_key = sys.argv[2]
    except IndexError:
        print("Usage: occurrence.py <species_id> <api_key>")
        quit()

    csv_filename = f"species_id{input_species_id}.csv"
    test_df = getdf(input_species_id, limit=-1, api_key=api_key)
    test_df.to_csv(csv_filename)

#!/usr/bin/env python3

import requests
import os
import sys

import numpy as np
import pandas as pd


URL_BASE = 'http://nas.er.usgs.gov/api/v1/'

def get_occurrence_header():
    """
    Returns a list of strings corresponding to the column names for occurrence queries
    """
    str_list = ['speciesID', 'group', 'family', 'genus', 'species', 'scientificName', 'commonName', 'state', 'county', 'locality', 'decimalLatitude', 'decimalLongitude', 'latLongSource', 'latLongAccuracy', 'Centroid Type', 'huc8Name', 'huc8', 'huc10Name', 'huc10', 'huc12Name', 'huc12', 'date', 'year', 'month', 'day', 'status', 'comments', 'recordType', 'disposal', 'museumCatNumber', 'freshMarineIntro', 'references']
    str_list = [name.lower().replace(' ', '').replace('_','') for name in str_list]
    return str_list

def getdf(species_id, keep_columns=None, limit=100, api_key=None):
    """
    Returns a pandas dataframe containing NAS query results for a given species ID
    """

    if api_key is not None:
        url_request = f"{URL_BASE}/occurrence/search?species_ID={species_id}&api_key={api_key}"
    else:
        url_request = f"{URL_BASE}/occurrence/search?species_ID={species_id}"
    
    request_json = requests.get(url_request, params={'limit':limit}).json()
    column_names = list(request_json['results'][0].keys())
    lower_columns = [name.lower().replace(' ','').replace('_','') for name in column_names]
    
    # Build a dictionary of column renamings for use in pandas rename function
    renamed_columns = {}
    for i in range(len(column_names)):
        renamed_columns[column_names[i]] = lower_columns[i]
    
    if keep_columns is None:
        keep_columns = list(renamed_columns.values())
    drop_columns = np.setdiff1d(list(renamed_columns.values()), keep_columns)
    
    request_df = pd.json_normalize(request_json, 'results')
    request_df = request_df.rename(columns=renamed_columns)
    request_df = request_df.drop(drop_columns, axis=1)
    #request_df = request_df.set_index('key')
    
    return request_df


def process_csv_df(csv_file, keep_columns=None):
    """
    Converts a manually downloaded CSV file from the NAS database into a pandas dataframe
    """

    csv_df = pd.read_csv(csv_file, low_memory=False)
    column_names = list(csv_df.columns)
    lower_columns = [name.lower().replace(' ','').replace('_','') for name in column_names]

    # Build a dictionary of column renamings for use in pandas rename function
    renamed_columns = {}
    for i in range(len(column_names)):
        renamed_columns[column_names[i]] = lower_columns[i]

    if keep_columns is None:
        keep_columns = list(renamed_columns.values())

    # TODO: Convert separate reference fields into a list of reference dictionaries
    # This is for compatibility with NAS API dataframes

    ref_column_names = [None] * 42
    for i in range(0, 42, 7):
        ref_column_names[i]   = f"reference{int((i+8)/7)}"
        ref_column_names[i+1] = f"type{int((i+8)/7)}"
        ref_column_names[i+2] = f"date{int((i+8)/7)}"
        ref_column_names[i+3] = f"author{int((i+8)/7)}"
        ref_column_names[i+4] = f"title{int((i+8)/7)}"
        ref_column_names[i+5] = f"publisher{int((i+8)/7)}"
        ref_column_names[i+6] = f"location{int((i+8)/7)}"

    # Always remove the separate reference fields
    for i in range(6):
        keep_columns.remove(f"reference{i+1}")
        keep_columns.remove(f"type{i+1}")
        keep_columns.remove(f"date{i+1}")
        keep_columns.remove(f"author{i+1}")
        keep_columns.remove(f"title{i+1}")
        keep_columns.remove(f"publisher{i+1}")
        keep_columns.remove(f"location{i+1}")
    
    drop_columns = np.setdiff1d(list(renamed_columns.values()), keep_columns)
    csv_df = csv_df.rename(columns=renamed_columns)
    csv_df = csv_df.drop(drop_columns, axis=1)
    
    return csv_df


def species_search(genus, species):
    """
    Returns NAS query results for a binomial name
    """
    
    url_request_species = f"{URL_BASE}/species/search?genus={genus}&species={species}"
    request_result = requests.get(url_request_species).json()
    return request_result['results']
    

def ref_counts(df):
    """
    Returns a pandas series for a df
    """
    return df['references'].value_counts().items()


def ref_string(ref_counts):
    """
    Returns a formatted string of information from a pandas series derived from NAS references
    """

    ref_string = ""
    ref_number = 1

    for ref_pair in ref_counts:
        ref_string +=  '--------\n'
        ref_string += f"Most common reference {ref_number}\n"
        ref_string += '\n'
        source_number = 1
    
        for ref in ref_pair[0]:
            ref_string += f"Source number:      {source_number}\n"
            ref_string += f"Title:              {ref['title']}\n"
            ref_string += f"Author:             {ref['author']}\n"
            ref_string += f"Publisher:          {ref['publisher']}\n"
            ref_string += f"Publisher Location: {ref['publisherLocation']}\n"
            ref_string += f"Year:               {ref['year']}\n"
            ref_string += f"Reference Type:     {ref['refType']}\n"
            ref_string += '\n'
            source_number += 1
    
        ref_string +=     f"Total Occurrences:  {ref_pair[1]}\n"
        ref_string += '--------\n'
        ref_string += '\n'
        ref_number += 1

    return ref_string


def species_string(species_list):
    """
    Returns a formatted string of information from a NAS search for a species
    """

    species_str = ""
    for species in species_list:
        for value in species:
            species_str += f"{value}: {species[value]}\n"
        species_str += '\n'
    return species_str

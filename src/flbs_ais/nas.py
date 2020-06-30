#!/usr/bin/env python3

import math
import requests
import os
import sys

import numpy as np
import pandas as pd


URL_BASE = 'http://nas.er.usgs.gov/api/v1/'


def get_col_rename(df, type):
    """
    Returns a dictionary of columns to rename based on the dataframe and type('csv' or 'api')
    """
    
    # Build a dictionary of column renamings for use in pandas rename function
    renamed_columns = {}
    column_names = list(df.columns)
    lower_columns = [name.lower().replace(' ','').replace('_','') for name in column_names]
    for i in range(len(column_names)):
        renamed_columns[column_names[i]] = lower_columns[i]

    if type == 'csv':
        # build csv rename dictionary
        renamed_columns['Latitude'] = 'decimallatitude'
        renamed_columns['Longitude'] = 'decimallongitude'
        renamed_columns['Museum_Cat_No'] = 'museumcatnumber'
        renamed_columns['HUC 8 Number'] = 'huc8'
        renamed_columns['Source'] = 'latlongsource'
        renamed_columns['Accuracy'] = 'latlongaccuracy'
    elif type == 'api':
        # build api rename dictionary
        renamed_columns['key'] = 'specimennumber'
    else:
        # error
        pass

    return renamed_columns


def get_header():
    """
    Returns a list of strings corresponding to the column names for occurrence queries
    """
    str_list = ['specimennumber','speciesid','group','family','genus','species','scientificname', \
                'commonname','country','state','county','locality','decimallatitude','decimallongitude', \
                'latlongsource','latlongaccuracy','drainagename','centroidtype','huc8name','huc8', \
                'huc10name','huc10','huc12name','huc12','date','year','month','day','status','comments', \
                'recordtype','disposal','museumcatnumber','freshmarineintro','references']
    return str_list


def getdf(species_id, keep_columns=None, limit=100, api_key=None):
    """
    Returns a pandas dataframe containing NAS query results for a given species ID
    """

    # Check for API key
    if api_key is not None:
        url_request = f"{URL_BASE}/occurrence/search?species_ID={species_id}&api_key={api_key}"
    else:
        url_request = f"{URL_BASE}/occurrence/search?species_ID={species_id}"
    
    # Get dataframe from API request
    request_json = requests.get(url_request, params={'limit':limit}).json()
    api_df = pd.json_normalize(request_json, 'results')

    # Add columns that are in a CSV dataframe but not an API dataframe
    api_df['country'] = np.nan
    api_df['drainagename'] = np.nan

    # Rename columns
    renamed_columns = get_col_rename(api_df, 'api')
    api_df = api_df.rename(columns=renamed_columns)

    # Reorder columns
    cols = list(api_df.columns)
    cols = cols[0:8] + cols[33:34] + cols[8:33] + cols[34:] # country
    cols = cols[0:16] + cols[34:] + cols[16:34] # drainagename
    api_df = api_df[cols]
    
    # Drop unwanted columns
    if keep_columns is None:
        keep_columns = list(renamed_columns.values())
    # TODO: Add error checking for invalid column names from user
    drop_columns = np.setdiff1d(list(renamed_columns.values()), keep_columns)
    api_df = api_df.drop(drop_columns, axis=1)
    
    return api_df


def process_csv_df(csv_file, keep_columns=None):
    """
    Converts a manually downloaded CSV file from the NAS database into a pandas dataframe
    """

    # Get dataframe from CSV file
    csv_df = pd.read_csv(csv_file, low_memory=False)
    
    # Add columns that are in an API dataframe but not a CSV dataframe
    csv_df['centroidtype'] = np.nan
    csv_df['date'] = np.nan
    csv_df['genus'] = np.nan
    csv_df['huc10name'] = np.nan
    csv_df['huc10'] = np.nan
    csv_df['huc12name'] = np.nan
    csv_df['huc12'] = np.nan
    csv_df['huc8name'] = np.nan
    csv_df['species'] = np.nan

    # Rename columns so both csv and api dataframes have identical headers
    renamed_columns = get_col_rename(csv_df, 'csv')
    csv_df = csv_df.rename(columns=renamed_columns)

    # Reorder columns
    cols = list(csv_df.columns)
    cols = cols[:4] + cols[69:70] + cols[75:76] + cols[4:69] + cols[70:75] # species and genus
    cols = cols[:17] + cols[69:70] + cols[17:69] + cols[70:] # centroidtype
    cols = cols[:18] + cols[75:] + cols[18:75] # huc8name
    cols = cols[:20] + cols[72:] + cols[20:72] # huc10name, huc10, huc12name, huc12
    cols = cols[:24] + cols[75:] + cols[24:75] # date
    csv_df = csv_df[cols]

    # Get list of columns to keep
    if keep_columns is None:
        keep_columns = list(renamed_columns.values())
    # TODO: Add error checking for invalid column names from user

    # Always remove the separate reference fields
    for i in range(6):
        keep_columns.remove(f"reference{i+1}")
        keep_columns.remove(f"type{i+1}")
        keep_columns.remove(f"date{i+1}")
        keep_columns.remove(f"author{i+1}")
        keep_columns.remove(f"title{i+1}")
        keep_columns.remove(f"publisher{i+1}")
        keep_columns.remove(f"location{i+1}")
    
    # Get list of columns to drop
    drop_columns = np.setdiff1d(list(renamed_columns.values()), keep_columns)

    # Convert separate reference fields into a list of reference dictionaries
    # This is for compatibility with NAS API dataframes
    ref_list_of_lists = [None] * len(csv_df)
    i = 0
    for row in csv_df.itertuples():
        ref_list = [None] * 6
        for j in range(6):
            # For each reference section in row, build a dict and add it to the list of dicts
            ref_dict = {}
            # Convert key and date to integer instead of float if existent
            ref_dict['key']       = int(row[35 + j * 7]) if not math.isnan(row[35 + j * 7]) else math.nan
            ref_dict['type']      = row[36 + j * 7]
            ref_dict['date']      = int(row[37 + j * 7]) if not math.isnan(row[37 + j * 7]) else math.nan
            ref_dict['author']    = row[38 + j * 7]
            ref_dict['title']     = row[39 + j * 7]
            ref_dict['publisher'] = row[40 + j * 7]
            ref_dict['location']  = row[41 + j * 7]
            ref_list[j] = ref_dict
        ref_list_of_lists[i] = ref_list
        i += 1

    # Add reference column and drop unwanted columns
    csv_df['references'] = ref_list_of_lists
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

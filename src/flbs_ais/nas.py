#!/usr/bin/env python3

import math
import requests
import os.path
import sys

from datetime import datetime
from os import path

import numpy as np
import pandas as pd


URL_BASE = 'http://nas.er.usgs.gov/api/v1/'


def api_df(species_id, limit, api_key):
    """Returns a pandas dataframe containing records about a species from the NAS database using their API"""
    
    # Check for API key
    if api_key is not None:
        url_request = f"{URL_BASE}/occurrence/search?species_ID={species_id}&api_key={api_key}"
    else:
        url_request = f"{URL_BASE}/occurrence/search?species_ID={species_id}"
    
    # Get dataframe from API request
    request_json = requests.get(url_request, params={'limit':limit}).json()
    api_df = pd.json_normalize(request_json, 'results')
    api_df = _manage_cols(api_df)

    # Add columns that are in a CSV dataframe but not an API dataframe
    api_df['country']      = np.nan
    api_df['drainagename'] = np.nan

    # Rename columns
    renamed_columns = _get_col_rename(api_df, 'api')
    api_df = api_df.rename(columns=renamed_columns)

    # Reorder columns
    cols = list(api_df.columns)
    cols = cols[0:8] + cols[33:34] + cols[8:33] + cols[34:] # country
    cols = cols[0:16] + cols[34:] + cols[16:34] # drainagename
    api_df = api_df[cols]
    
    return api_df


def csv_df(filename):
    """Returns a pandas dataframe containing records about a species from the NAS database using a downloaded CSV file"""

    # Get dataframe from CSV file
    csv_df = pd.read_csv(filename, low_memory=False)

    csv_df = _manage_cols(csv_df)
    
    # Add columns that are in an API dataframe but not a CSV dataframe
    csv_df['centroidtype'] = np.nan
    csv_df['date']         = np.nan
    csv_df['genus']        = np.nan
    csv_df['huc10name']    = np.nan
    csv_df['huc10']        = np.nan
    csv_df['huc12name']    = np.nan
    csv_df['huc12']        = np.nan
    csv_df['huc8name']     = np.nan
    csv_df['species']      = np.nan

    # Rename columns so both csv and api dataframes have identical headers
    renamed_columns = _get_col_rename(csv_df, 'csv')
    csv_df = csv_df.rename(columns=renamed_columns)
    
    # Reorder columns
    cols = list(csv_df.columns)
    cols = cols[:4] + cols[69:70] + cols[75:76] + cols[4:69] + cols[70:75] # species and genus
    cols = cols[:17] + cols[69:70] + cols[17:69] + cols[70:] # centroidtype
    cols = cols[:18] + cols[75:] + cols[18:75] # huc8name
    cols = cols[:20] + cols[72:] + cols[20:72] # huc10name, huc10, huc12name, huc12
    cols = cols[:24] + cols[75:] + cols[24:75] # date
    csv_df = csv_df[cols]

    # Change reference columns to single reference column
    csv_df = _convert_refs(csv_df)
    
    return csv_df


def modify_df(df, keep=None, drop=None, rename=None, refs=None, earth=False):
    """Returns a dataframe that has altered columns (dropped, renamed), is filtered for a subset of references, and is compatible with Google Earth Engine import"""
    
    df_dict = {}
    drop_list = []

    if drop and keep:
        if set(list(df.columns)) == set(drop + keep):
            drop_list = drop
        else:
            raise ValueError(f"Drop column list and keep column list do not combine to make set of all columns")
    elif drop:
        drop_list = drop
    elif keep:
        drop_list = np.setdiff1d(list(df.columns), keep)

    if earth:
        if rename and ( 'latitude' in list(rename.keys()) or 'longitude' in list(rename.keys()) ):
            raise ValueError("Can't rename latitude or longitude when Google Earth Engine import compatibility is true")
        # Create compatible date column
        df = _make_date_col(df)
    
    if refs:
        df = df[df.astype(str)['references'] != '[]']
        df['ref_key'] = df.references.map(lambda x: x[0]['key'])
        df = df[df.ref_key.isin(refs)]
        df = df.drop('ref_key', axis = 1)
    
    df_out = _manage_cols(df, drop_list, df_dict)

    return df_out


def csv_out(df, filepath='./', filename=None, overwrite=False):
    """Creates a CSV file using a generated name based on species and references, optionally overwriting or using a custom filename"""
    
    if filename == None:
        # Create generated filename
        filename = ''
        if 'commonname' in list(df.columns):
            filename += (df.iloc[0].commonname).lower().replace(' ','')
        else:
            filename += str(datetime.now())
    else:
        # TODO: Check if filename is good
        pass

    if overwrite == False:
        # Check if filename already exists
        filenumber = 0
        while path.exists(filepath + filename + str(filenumber)):
            filenumber += 1
        filename += f"_{filenumber}"
    
    df.to_csv(filepath + filename, index=False)


def get_header():
    """Returns a list of strings corresponding to the column names for occurrence queries"""
    str_list = ['specimennumber','speciesid','group','family','genus','species','scientificname', \
                'commonname','country','state','county','locality','latitude','longitude', \
                'source','accuracy','drainagename','centroidtype','huc8name','huc8', \
                'huc10name','huc10','huc12name','huc12','date','year','month','day','status','comments', \
                'recordtype','disposal','museumcatnumber','freshmarineintro','references']
    return str_list


def species(genus, species, output='list'):
    """Returns NAS query results for a binomial name. Output is either a string or a list of references"""
    url_request_species = f"{URL_BASE}/species/search?genus={genus}&species={species}"
    request_result = requests.get(url_request_species).json()
    species_list = request_result['results']

    if output == 'string':
        species_str = ""
        for species in species_list:
            for value in species:
                species_str += f"{value}: {species[value]}\n"
            species_str += '\n'
        return species_str
    elif output == 'list':
        return species_list
    else:
        raise ValueError(f"Invalid parameter for output '{output}' - Accepted values are 'list' or 'string'")



def references(df, sort='rank', ascending=True, output='list', limit=-1):
    """Returns a list of references for a dataframe. Sorts by alphabet or rank, in ascending or descending order.
    Output is either in a string or a list of references."""
    
    ref_counts = list(df['references'].value_counts().items())\

    if output == 'string':
        ref_string = ""
        if sort == 'rank':
            if ascending:
                ref_number = 1
            else:
                ref_number = len(ref_counts) + 1
            for ref_pair in ref_counts:
                if (ascending == True) and (limit != -1) and (ref_number > limit):
                    break
                elif (ascending == False) and (limit != -1) and (ref_number < (len(ref_counts) + 1 - limit)):
                    break
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
                    ref_string += f"Reference Key:      {ref['key']}\n"
                    ref_string += '\n'
                    source_number += 1
                ref_string +=     f"Total Occurrences:  {ref_pair[1]}\n"
                ref_string += '--------\n'
                ref_string += '\n'
                if ascending: 
                    ref_number += 1
                else:
                    ref_number -= 1
        elif sort == 'alphabet':
            # TODO: alphabetical sorting
            pass
        else:
            raise ValueError(f"Invalid parameter for sort '{sort}' - Accepted values are 'rank' or 'alphabet'")
        return ref_string
    elif output == 'list':
        return ref_counts
    else:
        raise ValueError(f"Invalid parameter for output '{output}' - Accepted values are 'list' or 'string'")



def _get_col_rename(df, dftype):
    """Returns a dictionary of columns to rename based on the dataframe and type('csv' or 'api')"""
    
    # Build a dictionary of column renamings for use in pandas rename function
    renamed_columns = {}
    column_names = list(df.columns)
    lower_columns = [name.lower().replace(' ','').replace('_','') for name in column_names]
    for i in range(len(column_names)):
        renamed_columns[column_names[i]] = lower_columns[i]

    if dftype == 'csv':
        # build csv rename dictionary
        renamed_columns['museumcatno'] = 'museumcatnumber'
        renamed_columns['huc8number']  = 'huc8'
    elif dftype == 'api':
        # build api rename dictionary
        renamed_columns['key']              = 'specimennumber'
        renamed_columns['decimallatitude']  = 'latitude'
        renamed_columns['decimallongitude'] = 'longitude'
        renamed_columns['latlongsource']    = 'source'
        renamed_columns['latlongaccuracy']  = 'accuracy'
    else:
        raise ValueError(f"Dataframe type '{dftype}' invalid - Accepted inputs are 'csv' or 'api'")

    return renamed_columns


def _convert_refs(df):
    drop_list = []

    # Always remove the separate reference fields
    for i in range(6):
        drop_list.append(f"reference{i+1}")
        drop_list.append(f"type{i+1}")
        drop_list.append(f"date{i+1}")
        drop_list.append(f"author{i+1}")
        drop_list.append(f"title{i+1}")
        drop_list.append(f"publisher{i+1}")
        drop_list.append(f"location{i+1}")

    # Convert separate reference fields into a list of reference dictionaries
    # This is for compatibility with NAS API dataframes
    ref_list_of_lists = [None] * len(df)
    i = 0
    for row in df.itertuples():
        ref_list = []
        for j in range(6):
            # For each reference section in row, build a dict and add it to the list of dicts
            ref_dict = {}
            # Convert key and date to integer instead of float if existent
            ref_dict['key'] = int(row[35 + j * 7]) if not math.isnan(row[35 + j * 7]) else math.nan
            if not math.isnan(ref_dict['key']):
                ref_dict['refType']           = row[36 + j * 7]
                ref_dict['year']              = int(row[37 + j * 7]) if not math.isnan(row[37 + j * 7]) else math.nan
                ref_dict['author']            = row[38 + j * 7]
                ref_dict['title']             = row[39 + j * 7]
                ref_dict['publisher']         = row[40 + j * 7]
                ref_dict['publisherLocation'] = row[41 + j * 7]
                ref_list.append(ref_dict)
            else:
                break
        ref_list_of_lists[i] = ref_list
        i += 1

    # Add reference column and drop unwanted columns, rename
    df['references'] = ref_list_of_lists
    df = df.drop(drop_list, axis=1)

    return df


def _make_date_col(df):
    df = df.fillna(1)
    df['date'] = pd.to_datetime(df.year*10000 + df.month*100 + df.day, format='%Y%m%d')
    return df 


def _manage_cols(df, drop_list=[], name_dict={}):
    """Private method for dropping and renaming columns in a dataframe, as well as creating one standard table from two different forms."""

    for colname in drop_list:
        if colname not in df:
            raise ValueError(f"Can't drop column '{colname}' - '{colname}' does not exist in dataframe")
    for colname in list(name_dict.keys()):
        if colname not in df:
            raise ValueError(f"Can't rename '{colname}' to '{name_dict[colname]}' - '{colname}' does not exist in dataframe")
        if colname in drop_list:
            raise ValueError(f"Can't rename '{colname}' to '{name_dict[colname]}' - '{colname}' in drop_list")

    column_names = np.setdiff1d(list(df.columns), list(name_dict.keys()))
    lower_columns = [name.lower().replace(' ','').replace('_','') for name in column_names]
    for i in range(len(column_names)):
        name_dict[column_names[i]] = lower_columns[i]
    
    df = df.drop(drop_list, axis=1)
    df = df.rename(columns=name_dict)
    
    return df

#!/usr/bin/env python3

"""
Given a species ID, this script returns all occurrences of this species from
the NAS database and puts the results into a csv file.
Note: At the moment, this can only create a csv file with 100 rows
"""

import csv
import requests

url_base = 'http://nas.er.usgs.gov/api/v1/'

if __name__ == "__main__":
    input_species_id = input('Enter species_id: ')
    url_request_species = f"{url_base}/occurrence/search?species_ID={input_species_id}"
    request_result = requests.get(url_request_species, params={'limit':100}).json()
    
    # TODO: Fix ugly way of removing references/Add support for selecting columns
    #fieldnames = request_result['results'][0].keys()
    fieldnames = list(request_result['results'][0])
    if ('references' in fieldnames):
        fieldnames.remove('references')

    csv_filename = f"species_id{input_species_id}.csv"
    with open(csv_filename, 'w', newline='\n') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csv_writer.writeheader()
        for occurrence in request_result['results']:
            new_row = {}
            for key in occurrence:
                if key != 'references':
                    new_row[key] = occurrence[key]
            csv_writer.writerow(new_row)
    

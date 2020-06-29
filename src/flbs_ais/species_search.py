#!/usr/bin/env python3

import requests

#import sys
#print(sys.version)

url_base = 'http://nas.er.usgs.gov/api/v1/'

def search(genus, species):
    pass

if __name__ == "__main__":
    input_species = input('Enter binomial species name: ')
    binomial_split = input_species.split(' ')
    name_genus = binomial_split[0]
    name_species = binomial_split[1]
    
    url_request_species = f"{url_base}/species/search?genus={name_genus}&species={name_species}"
    request_result = requests.get(url_request_species).json()

    print('Results of Search:')
    print(f"  endOfRecords: {request_result['endOfRecords']}")
    print(f"  count: {request_result['count']}")
    print(f"  offset: {request_result['offset']}")
    print(f"  limit: {request_result['limit']}")
    print('  Species list:')
    for species in request_result['results']:
        for value in species:
            print(f"    {value}: {species[value]}")
        print()
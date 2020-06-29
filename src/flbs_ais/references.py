#!/usr/bin/env python3

"""
Return a list of most common references documenting species occurrences
"""

import os
import sys
import pandas as pd
import occurrence

def ref_string(df):
    """
    Print the most common references in descending order from a compatible pd dataframe
    """
    ref_string = ""
    ref_result_list = df['references'].value_counts().items()
    ref_number = 1
    for ref_pair in ref_result_list:
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

if __name__ == "__main__":
    user_api_key = sys.argv[1]
    user_species_id = sys.argv[2]
    user_df = occurrence.getdf(user_species_id, limit=-1, api_key=user_api_key)
    with open(f"ref_results_{user_species_id}.txt", 'w') as file:
        file.write(ref_string(user_df))

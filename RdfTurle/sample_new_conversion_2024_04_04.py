import json
import csv
import pandas as pd

import triple_creation_from_list_function, Fileter_unique_triples_fucntion


# Load CSV file
csv_file_path = 'Gauge_attributes.csv'
with open(csv_file_path, newline='') as csvfile:
    csv_reader = csv.reader(csvfile, delimiter=';')

    # Read the header row
    headers = next(csv_reader)
    #print(headers)


# reading the JSON file
json_file_path = 'mapping_test_2.json'

with open(json_file_path, 'r') as file:
    json_data = json.load(file)

    json_all_keys = []

    for json_key in json_data:
        json_all_keys.append(json_key)


    #print(json_all_keys)



#try to use datafrme
csf_file_data_frame = pd.read_csv(csv_file_path, delimiter=';')

# Get the list of column headings from the DataFrame
column_headings = csf_file_data_frame.columns.tolist()

#print(type(column_headings))


# Initialize a list to store confirmed matches
confirmed_matches = []

# Iterate over the words to match
for key in json_all_keys:
    # Check if there is an exact match
    if key in column_headings:
        confirmed_matches.append(key)

print(confirmed_matches)


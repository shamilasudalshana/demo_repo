import json
import csv
import pandas as pd

import triple_creation_from_list_function, Fileter_unique_triples_fucntion, triple_creation_from_string_function
import observation_mapping_function, time_variables_creation_from_csv_funtion,mapping_prefixes_fuction


# Load CSV file
csv_file_path = 'Gauge_attributes.csv'
with open(csv_file_path, newline='') as csvfile:
    csv_reader = csv.reader(csvfile, delimiter=';')

    # Read the header row
    headers = next(csv_reader)
    #print(headers)


# reading the JSON file related to observation time
time_json_path = 'mapping_time.json'

# reading the JSON file with vocabularies
json_file_path = 'mapping_test_2.json'

# reading the JSON file with prefixes dictionary
prefixes_dictionary_path  = 'prefixes_dic.json'


# creation of output Turtle file name (removal of CSV extension and add .ttl extension)
output_turtle_file = csv_file_path.split(".")[0] + ".ttl"


with open(json_file_path, 'r') as file:
    json_data = json.load(file)

    json_all_keys = []

    for json_key in json_data:
        json_all_keys.append(json_key)


    #print(json_all_keys)

is_observation_file = input(f"Is {csv_file_path} a observation file? (Y or N) : ").lower()



if is_observation_file == "y" :
    sensor_ID = int(input(f"Please inset the sensor ID of the observation file - {csv_file_path} : "))
    is_attribute_file = "n" # making as automatic adjustment this is not a attribute file

else:
    is_attribute_file = input(f"Is {csv_file_path} a attribute file? (Y or N) : ").lower()


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

#print(confirmed_matches)

# take the length of Json values for each keys
for key, value in json_data.items():

    if isinstance(value, list):
        #print(f'"{key}" - {len(value)}')
        key_value_length = len(value)

    else:
        #print(f'"{key}" - 1')
        key_value_length = 1

    #print(f'{key} - length is {key_value_length}')

# take whether 1st string of triple need to print or Indentation
is_new_line_to_print = True

all_triples = []

# Extract and print data for matched headings
for index, row in csf_file_data_frame.iterrows():
    #print(f"\nRow {index + 1} - Matched Headings:")


    # providing the unique ID for sensor with the ontology term
    sensor_designation = json_data['sensorDesignation'][0] + str(index + 1)

    # print the initial sensor definition
    triple_string_1 = sensor_designation

    triple_string_2 = json_data['sensorDesignation'][1]
    triple_string_3 = json_data['sensorDesignation'][2]

    sensor_definition = [triple_string_1, triple_string_2, triple_string_3]

    all_triples.append(sensor_definition)

    #if is_observation_file == "y":




    converted_heading=[]  # create an empty list initially for converted headings


    i = -1
    for index_of_iterating_column, heading in enumerate(confirmed_matches):
        column = row[heading]

        #print(f"heading: {heading}")

        if is_attribute_file == "y":

            matched_vocabulary_from_JSON = json_data[heading]
            element = json_data['sensorDesignation'][0]
            identification_number = index + 1
            value_from_csv = column


            if isinstance(matched_vocabulary_from_JSON, list):
                i = i + 1

                triple_creation_from_list_function.process_given_list(matched_vocabulary_from_JSON, element, identification_number, value_from_csv, all_triples)

            elif isinstance(matched_vocabulary_from_JSON, str):
                i = i + 1

                triple_creation_from_string_function.process_given_string(matched_vocabulary_from_JSON, element,identification_number, value_from_csv, all_triples)

        elif is_observation_file == "y":
            print("this is observation file\n"
                  f"this is the vocabulary : {json_data[heading]} ")

            matched_vocabulary_from_JSON = json_data[heading]
            element = json_data['observation_designation'][0]
            value_from_csv = value
            has_result_term = "sosa:hasResult"
            has_sim_result_term = "sosa:hasSimpleResult"
            result_time_term = "sosa:resultTime"
            observation_definition = "n4e_hyd:observation_"
            made_by_sensor_term = "sosa:madeBySensor"
            number_of_obervations_per_row = len(confirmed_matches)

            observation_no = index * number_of_obervations_per_row + (index_of_iterating_column + 1)

            observation_date_time = time_variables_creation_from_csv_funtion.parse_csv_row(csv_file_path, time_json_path, index)
            print(f'observation no {observation_no} on {observation_date_time} for {heading}')

            observation_mapping_function.observation_maping(matched_vocabulary_from_JSON, observation_date_time, sensor_ID, all_triples,
                                      observation_definition, result_time_term, has_result_term, has_sim_result_term,
                                      observation_no, value_from_csv)

            print(matched_vocabulary_from_JSON)



# delete the duplicate triples.
unique_triples = Fileter_unique_triples_fucntion.get_unique_triples(all_triples)


# printing the prefixes
#mapping_prefixes_fuction.print_prefixes('prefixes_dic.json', unique_triples)

import print_RDF_in_turtle_file_fuction

print_RDF_in_turtle_file_fuction.write_triples_to_turtle(unique_triples,prefixes_dictionary_path, output_turtle_file)


print()
print(f"Note:\n\tinitial no of triples {len(all_triples)}.\n\tafter removal of duplicate triples available no of "
      f"triples {len(unique_triples)}")







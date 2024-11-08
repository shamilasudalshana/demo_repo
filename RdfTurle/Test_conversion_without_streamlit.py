import json
import pandas as pd
from io import StringIO
import time

# Import custom functions
import triple_creation_from_list_function
import Fileter_unique_triples_fucntion
import triple_creation_from_string_function
import observation_mapping_function
import time_variables_creation_from_csv_funtion
import print_RDF_in_turtle_file_fuction
from extract_sensor_id_from_file_fuciton import extract_sensor_id
from categorize_file_function import categorize_file
from check_values_in_a_list_fucntion import check_values_in_list
from format_floats_DF_readed_values_function import format_floats_to_string
from delimeter_selection_funciton import delimiter_selection


# Helper function to load JSON data from a file
def load_json(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return None


# Helper function to save an uploaded file and return its path
def save_file(file):
    try:
        file_path = file.name
        with open(file_path, 'wb') as f:
            f.write(file.getbuffer())
        return file_path
    except Exception as e:
        print(f"Error saving file: {e}")
        return None


# Helper function to combine multiple JSON files into one dictionary
def combine_json_files(json_file_paths):
    combined_data = {}
    for file_path in json_file_paths:
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    combined_data.update(data)
            except Exception as e:
                print(f"Error combining JSON file {file_path}: {e}")
    return combined_data


# Function to process the CSV file and generate RDF triples
def process_csv_file(csv_content, mapping_json_data, prefixes_json_data, time_data_json, is_time_dependant_csv,
                     sensor_ID_column_heading, delimiter, csv_file_name, parsing_method, date_col, time_col,
                     date_format, time_format):
    all_triples = []

    try:
        csv_file_data_frame = pd.read_csv(StringIO(csv_content), delimiter=delimiter)
    except pd.errors.EmptyDataError:
        print("No columns to parse from file. Please check the delimiter and the file content.")
        return None
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

    column_headings = csv_file_data_frame.columns.tolist()
    confirmed_matches = [key for key in mapping_json_data.keys() if key in column_headings]
    no_of_inputs = 0

    for index, row in csv_file_data_frame.iterrows():
        sensor_ID = format_floats_to_string(row[sensor_ID_column_heading])
        sensor_designation = mapping_json_data['sensorDesignation'][0] + sensor_ID
        sensor_definition = [sensor_designation, mapping_json_data['sensorDesignation'][1],
                             mapping_json_data['sensorDesignation'][2]]
        all_triples.append(sensor_definition)

        for index_of_iterating_column, heading in enumerate(confirmed_matches):
            cell_value = row[heading]
            no_of_inputs += 1
            matched_vocabulary_from_mapping_json = mapping_json_data[heading]

            if not is_time_dependant_csv:
                element = mapping_json_data['sensorDesignation'][0]
                identification_number = sensor_ID

                if isinstance(matched_vocabulary_from_mapping_json, list):
                    triple_creation_from_list_function.process_given_list(
                        matched_vocabulary_from_mapping_json, element, identification_number, cell_value, all_triples)
                elif isinstance(matched_vocabulary_from_mapping_json, str):
                    triple_creation_from_string_function.process_given_string(
                        matched_vocabulary_from_mapping_json, element, identification_number, cell_value, all_triples)
            else:
                element = mapping_json_data['observation_designation'][0]
                has_result_term = "sosa:hasResult"
                has_sim_result_term = "sosa:hasSimpleResult"
                result_time_term = "sosa:resultTime"
                observation_definition = "n4e_hyd:observation_"

                observation_no = (index * len(confirmed_matches) + (index_of_iterating_column + 1))
                observation_date_time = time_variables_creation_from_csv_funtion.parse_csv_row(
                    csv_content, time_data_json, index, parsing_method, delimiter, date_col, time_col, date_format,
                    time_format)
                observation_mapping_function.observation_mapping(
                    matched_vocabulary_from_mapping_json, observation_date_time, sensor_ID, all_triples,
                    observation_definition, result_time_term, has_result_term, has_sim_result_term,
                    observation_no, cell_value)

    unique_triples = Fileter_unique_triples_fucntion.get_unique_triples(all_triples)
    output_turtle_file = csv_file_name.split(".")[0] + ".ttl"
    print_RDF_in_turtle_file_fuction.write_triples_to_turtle(unique_triples, prefixes_json_data, output_turtle_file)
    print(f"No of inputs converted : {no_of_inputs}")
    return output_turtle_file, len(unique_triples)


# Main function to load and process files
def main(csv_files, mapping_json_files, prefixes_json_files, time_data_json_path, sensor_ID_column_heading):
    mapping_json_data = combine_json_files(mapping_json_files)
    prefixes_json_data = combine_json_files(prefixes_json_files)
    time_data_json = load_json(time_data_json_path)

    for csv_file in csv_files:
        csv_content = open(csv_file, 'r').read()
        delimiter = delimiter_selection(csv_file)

        is_time_dependant_csv = False
        parsing_method, date_col, time_col, date_format, time_format = None, None, None, None, None

        output_turtle_file, num_triples = process_csv_file(
            csv_content, mapping_json_data, prefixes_json_data, time_data_json,
            is_time_dependant_csv, sensor_ID_column_heading, delimiter, csv_file,
            parsing_method, date_col, time_col, date_format, time_format)

        if output_turtle_file:
            print(f"Turtle file created: {output_turtle_file}")
            print(f"Number of triples generated: {num_triples}")


# usage of the files
if __name__ == "__main__":
    csv_files = ["Gauge_attributes.csv"]  # CSV files paths
    mapping_json_files = ["mapping_test_2.json"]  # JSON mapping JSON file name or path
    prefixes_json_files = ["prefixes_dic - Copy.json"]  #  prefixes JSON file or path
    time_data_json_path = "mapping_time.json"  #time JSON data file name or path
    sensor_ID_column_heading = "ID"  # mention this properlu sensor ID column name in the CSV

    main(csv_files, mapping_json_files, prefixes_json_files, time_data_json_path, sensor_ID_column_heading)

import pandas as pd
import json
from pyproj import Transformer
import os

# Import custom functions
import triple_creation_from_list_function
import Fileter_unique_triples_fucntion
import triple_creation_from_string_function
import observation_mapping_function
import time_variables_creation_from_csv_funtion
import print_RDF_in_turtle_file_fuction
from format_floats_DF_readed_values_function import format_floats_to_string


# input variables for the configuration
csv_file_path = "Gauge_attributes.csv"  # Path to the CSV file
delimiter = ";"  # provide the  delimiter - default for LamaH is ';' but when a change is done and save it is ','
mapping_json_path = "mapping_test_3.json"  # Path to the mapping JSON file
prefixes_json_path = "prefixes_dic - Copy.json"  # Path to the prefixes JSON file
#output_turtle_file_name = "output.ttl"  # Name for the output Turtle file
coordinate_columns = {"x_col": "lon", "y_col": "lat"}  # Column names for coordinates
input_epsg = "EPSG:3035"  # Input EPSG code for coordinate transformation
output_epsg = "EPSG:4326"  # Target EPSG code (WGS 84)
sensor_ID_column = "ID"  # Default sensor ID column name
is_time_dependant_csv = False  # Whether the CSV is time-dependent

# generation the Turtle file name from the CSV file name
output_turtle_file_name = os.path.splitext(os.path.basename(csv_file_path))[0] + ".ttl"


# Load JSON files
def load_json(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return None


# Transform coordinates
def transform_coordinates(dataframe, x_col, y_col, input_epsg, output_epsg):
    transformer = Transformer.from_crs(input_epsg, output_epsg, always_xy=True)
    dataframe[[x_col, y_col]] = dataframe.apply(
        lambda row: transformer.transform(row[x_col], row[y_col]),
        axis=1,
        result_type="expand"
    )
    return dataframe


# Process CSV to generate RDF triples
def process_csv_file(dataframe, mapping_json_data, prefixes_json_data, is_time_dependant_csv, sensor_ID_column, output_turtle_file):
    all_triples = []

    if sensor_ID_column not in dataframe.columns:
        raise ValueError(f"Sensor ID column '{sensor_ID_column}' does not exist in the DataFrame.")

    column_headings = dataframe.columns.tolist()
    confirmed_matches = [key for key in mapping_json_data.keys() if key in column_headings]
    no_of_inputs = 0

    for index, row in dataframe.iterrows():
        sensor_ID = format_floats_to_string(row[sensor_ID_column])
        sensor_designation = mapping_json_data['sensorDesignation'][0] + sensor_ID
        sensor_definition = [sensor_designation, mapping_json_data['sensorDesignation'][1], mapping_json_data['sensorDesignation'][2]]
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
                    dataframe, None, index, None, None, None, None, None
                )
                observation_mapping_function.observation_mapping(
                    matched_vocabulary_from_mapping_json, observation_date_time, sensor_ID, all_triples,
                    observation_definition, result_time_term, has_result_term, has_sim_result_term,
                    observation_no, cell_value)

    unique_triples = Fileter_unique_triples_fucntion.get_unique_triples(all_triples)
    print_RDF_in_turtle_file_fuction.write_triples_to_turtle(unique_triples, prefixes_json_data, output_turtle_file)
    print(f"No of inputs converted: {no_of_inputs}")
    print(f"Turtle file generated: {output_turtle_file}")


# Main execution workflow
def main():
    print("Loading CSV file...")
    try:
        csv_file_data_frame = pd.read_csv(csv_file_path, delimiter=delimiter)
    except Exception as e:
        print(f"Error reading the CSV file: {e}")
        return

    print("CSV file loaded successfully. Preview:")
    print(csv_file_data_frame.head())

    # Load JSON files
    print("Loading JSON files...")
    mapping_json_data = load_json(mapping_json_path)
    prefixes_json_data = load_json(prefixes_json_path)
    if not mapping_json_data or not prefixes_json_data:
        print("Error: Failed to load one or more JSON files.")
        return

    # Transform coordinates if needed
    if coordinate_columns["x_col"] in csv_file_data_frame.columns and coordinate_columns["y_col"] in csv_file_data_frame.columns:
        print("Transforming coordinates to WGS 84...")
        csv_file_data_frame = transform_coordinates(
            csv_file_data_frame,
            coordinate_columns["x_col"],
            coordinate_columns["y_col"],
            input_epsg,
            output_epsg
        )
        print("Coordinates transformed successfully.")
        print(csv_file_data_frame.head())
    else:
        print("Warning: Coordinate columns not found. Skipping coordinate transformation.")

    # Process the CSV file to generate RDF triples
    print("Processing CSV file to generate RDF triples...")
    try:
        process_csv_file(
            dataframe=csv_file_data_frame,
            mapping_json_data=mapping_json_data,
            prefixes_json_data=prefixes_json_data,
            is_time_dependant_csv=is_time_dependant_csv,
            sensor_ID_column=sensor_ID_column,
            output_turtle_file=output_turtle_file_name
        )
    except Exception as e:
        print(f"Error during RDF conversion: {e}")


if __name__ == "__main__":
    main()

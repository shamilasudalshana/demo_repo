import streamlit as st
import json
import pandas as pd
from io import StringIO
import time
from pyproj import Transformer

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
from transform_coordinates_func import transform_coordinates


def load_json(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        st.error(f"Error loading JSON file: {e}")
        return None


def save_file(file):
    try:
        file_path = file.name
        with open(file_path, 'wb') as f:
            f.write(file.getbuffer())
        return file_path
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None


def combine_json_files(json_file_paths):
    combined_data = {}
    for file_path in json_file_paths:
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    combined_data.update(data)
            except Exception as e:
                st.error(f"Error combining JSON file {file_path}: {e}")
    return combined_data


def process_csv_file(dataframe, mapping_json_data, prefixes_json_data, time_data_json, is_time_dependant_csv,
                     sensor_ID_column_heading, csv_file_name, parsing_method, date_col, time_col, date_format, time_format):
    """
    Processes the given DataFrame and generates RDF triples.

    Parameters:
        dataframe (pd.DataFrame): The DataFrame to process.
        mapping_json_data (dict): Mapping JSON data.
        prefixes_json_data (dict): Prefixes JSON data.
        time_data_json (dict): Time-related JSON data (if applicable).
        is_time_dependant_csv (bool): Indicates if the CSV is time-dependent.
        sensor_ID_column_heading (str): The column containing sensor IDs.
        csv_file_name (str): The name of the CSV file (used for output naming).
        parsing_method, date_col, time_col, date_format, time_format: Time parsing configurations (if applicable).

    Returns:
        tuple: (output_turtle_file, number_of_triples) or None if there's an error.
    """
    all_triples = []

    if sensor_ID_column_heading not in dataframe.columns:
        st.error(f"Selected sensor ID column '{sensor_ID_column_heading}' does not exist in the DataFrame.")
        return None

    column_headings = dataframe.columns.tolist()
    confirmed_matches = [key for key in mapping_json_data.keys() if key in column_headings]
    no_of_inputs = 0

    for index, row in dataframe.iterrows():
        sensor_ID = format_floats_to_string(row[sensor_ID_column_heading])
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
                    dataframe, time_data_json, index, parsing_method, date_col, time_col, date_format, time_format)
                observation_mapping_function.observation_mapping(
                    matched_vocabulary_from_mapping_json, observation_date_time, sensor_ID, all_triples,
                    observation_definition, result_time_term, has_result_term, has_sim_result_term,
                    observation_no, cell_value)

    unique_triples = Fileter_unique_triples_fucntion.get_unique_triples(all_triples)
    output_turtle_file = csv_file_name.split(".")[0] + ".ttl"
    print_RDF_in_turtle_file_fuction.write_triples_to_turtle(unique_triples, prefixes_json_data, output_turtle_file)
    st.write(f"No of inputs converted: {no_of_inputs}")
    return output_turtle_file, len(unique_triples)


def home_page():
    st.title("HydroTurtle - RDF Turtle Converter")
    st.image("NFDI4Earth_logo.png", width=450)

    csv_files = st.file_uploader("Upload CSV files", type=["csv"], accept_multiple_files=True)
    mapping_json_files = st.file_uploader("Upload Mapping JSON files", type=['json'], accept_multiple_files=True)
    prefixes_json_files = st.file_uploader("Upload Prefixes JSON files", type=["json"], accept_multiple_files=True)

    if csv_files and mapping_json_files and prefixes_json_files:
        mapping_json_file_paths = [save_file(f) for f in mapping_json_files]
        prefixes_json_file_paths = [save_file(f) for f in prefixes_json_files]
        combined_prefixes_json_data = combine_json_files(prefixes_json_file_paths)

        for csv_file in csv_files:
            # Initialize or retrieve the DataFrame in session state
            if f"{csv_file.name}_data_frame" not in st.session_state:
                csv_content = csv_file.getvalue().decode("utf-8")
                delimiter = delimiter_selection(csv_file)
                try:
                    csv_file_data_frame = pd.read_csv(StringIO(csv_content), delimiter=delimiter)
                    st.session_state[f"{csv_file.name}_data_frame"] = csv_file_data_frame
                except Exception as e:
                    st.error(f"Error reading the file with the selected delimiter: {e}")
                    continue

            # Always work with the DataFrame from session state
            csv_file_data_frame = st.session_state[f"{csv_file.name}_data_frame"]

            # Display the DataFrame
            st.write(f"Preview of '{csv_file.name}':")
            st.dataframe(csv_file_data_frame.head())

            # Allow user to specify if the file has coordinates
            has_coordinates = st.radio(
                f"Does the dataset '{csv_file.name}' contain coordinates?",
                options=["Yes", "No"],
                index=1  # Default to "No"
            ) == "Yes"

            if has_coordinates:
                is_wgs84_coordinate = st.radio(
                    f"Are the coordinates in '{csv_file.name}' already in WGS 84?",
                    options=["Yes", "No"],
                    index=0
                ) == "Yes"

                if not is_wgs84_coordinate:
                    x_col = st.selectbox(f"Select the column for Longitude (x) in '{csv_file.name}':", csv_file_data_frame.columns)
                    y_col = st.selectbox(f"Select the column for Latitude (y) in '{csv_file.name}':", csv_file_data_frame.columns)
                    input_epsg = st.text_input(f"Enter the EPSG code of the input CRS (e.g., 3035):", "3035")

                    if st.button(f"Transform Coordinates for {csv_file.name}"):
                        try:
                            csv_file_data_frame = transform_coordinates(
                                csv_file_data_frame, x_col, y_col, f"EPSG:{input_epsg}", "EPSG:4326"
                            )
                            st.session_state[f"{csv_file.name}_data_frame"] = csv_file_data_frame
                            st.success(f"Coordinates in '{csv_file.name}' transformed to WGS 84!")
                        except Exception as e:
                            st.error(f"Error during transformation: {e}")

            # Update DataFrame in session state after each widget interaction
            csv_file_data_frame = st.session_state[f"{csv_file.name}_data_frame"]

            # Display updated DataFrame
            st.write(f"Updated DataFrame for '{csv_file.name}':")
            st.dataframe(csv_file_data_frame.head())

            # Select mapping JSON and process the file
            selected_mapping_json_file = st.selectbox(f"Select mapping JSON file for {csv_file.name}", mapping_json_file_paths)
            mapping_json_data = load_json(selected_mapping_json_file)

            sensor_ID_column_heading = st.selectbox("Select the ID column of the sensor/measurement station:", csv_file_data_frame.columns)

            if st.button(f"Convert {csv_file.name} to Turtle"):
                result = process_csv_file(
                    csv_file_data_frame, mapping_json_data, combined_prefixes_json_data, None, False,
                    sensor_ID_column_heading, csv_file.name, None, None, None, None, None
                )
                if result:
                    output_turtle_file, num_triples = result
                    st.success(f"Turtle file created: {output_turtle_file}")
                    st.download_button(label="Download Turtle file", data=open(output_turtle_file).read(), file_name=output_turtle_file)




# Main function
def main():
    st.sidebar.title("Navigation Panel")
    page = st.sidebar.radio("Go to", ['Home', 'Settings', 'About'])

    if page == "Home":
        home_page()
    elif page == "Settings":
        st.write("Settings page")
    elif page == "About":
        st.write("About page")


if __name__ == "__main__":
    main()
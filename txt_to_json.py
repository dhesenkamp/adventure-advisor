import json
import os
import re

def jsonp_to_json(jsonp_string):
    # Use regex to extract the JSON part from the JSONP string
    match = re.search(r'\(({.*})\)', jsonp_string)
    if match:
        json_str = match.group(1)
        try:
            # Parse the JSON string into a Python dictionary
            json_data = json.loads(json_str)
            return json_data
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return None
    else:
        print("No JSON data found in the JSONP string.")
        return None

def process_file(input_file_path, output_file_path):
    # Read the content of the input file
    with open(input_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Convert JSONP to JSON
    json_data = jsonp_to_json(content)
    if json_data is not None:
        # Write the JSON data to the output file
        with open(output_file_path, 'w', encoding='utf-8') as file:
            json.dump(json_data, file, indent=4, ensure_ascii=False)
        print(f"Successfully converted {input_file_path} to {output_file_path}")
    else:
        print(f"Failed to convert {input_file_path}")

def process_directory(directory):
    # Iterate over all files in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            input_file_path = os.path.join(directory, filename)
            output_file_path = os.path.join(directory, filename.replace('.txt', '.json'))
            process_file(input_file_path, output_file_path)


process_directory(r"C:\Users\luzie\OneDrive\Desktop\Studium\Master\2. Semester\Designing Large Scale AI Systems\adventure-advisor\tour_jsons")
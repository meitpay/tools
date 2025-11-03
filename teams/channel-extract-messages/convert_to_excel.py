import pandas as pd
import ijson
import os
import argparse # Import the argparse library

def flatten_json_object(json_obj):
    """
    Flattens a single JSON object with nested structures.
    Example: {'a': 1, 'b': {'c': 2}} becomes {'a': 1, 'b_c': 2}
    """
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            view_alert_url = ''
            view_query_url = ''
            for item in x:
                if isinstance(item, dict) and 'title' in item and 'url' in item:
                    if item['title'] == 'View Alert':
                        view_alert_url = item['url']
                    elif item['title'] == 'View Query Results':
                        view_query_url = item['url']
            out['actions_view_alert_url'] = view_alert_url
            out['actions_view_query_results_url'] = view_query_url
        else:
            out[name[:-1]] = x

    flatten(json_obj)
    return out

def json_to_excel_streaming(json_file_path, excel_file_path):
    """
    Reads a large JSON file using a streaming parser and converts it to an Excel file.

    Args:
        json_file_path (str): The path to the input JSON file.
        excel_file_path (str): The path where the output Excel file will be saved.
    """
    if not os.path.exists(json_file_path):
        print(f"Error: Input file not found at '{json_file_path}'")
        return

    print(f"Starting conversion of '{json_file_path}' to '{excel_file_path}'...")

    def record_generator():
        with open(json_file_path, 'rb') as f:
            for record in ijson.items(f, 'item'):
                yield flatten_json_object(record)

    try:
        df = pd.DataFrame(record_generator())
        print(f"Successfully processed {len(df)} records.")

        desired_columns = [
            'createdDateTime', 'card_severity', 'card_alertTitle', 'card_messageTitle',
            'sender', 'card_firedAt', 'card_metricName', 'card_metricValue',
            'card_threshold', 'card_resource', 'messageId', 'actions_view_alert_url',
            'actions_view_query_results_url'
        ]
        
        existing_columns = [col for col in desired_columns if col in df.columns]
        df = df[existing_columns]

        df.to_excel(excel_file_path, index=False, engine='openpyxl')
        print(f"Conversion complete. Excel file saved to '{excel_file_path}'")

    except Exception as e:
        print(f"An error occurred during the conversion: {e}")

# --- Main execution block ---
if __name__ == "__main__":
    # 1. Set up the argument parser
    parser = argparse.ArgumentParser(
        description="Convert a large, structured JSON file to an Excel file.",
        formatter_class=argparse.RawTextHelpFormatter # For better help text formatting
    )
    
    # 2. Define the command-line arguments
    parser.add_argument(
        "input_file", 
        help="Path to the source JSON file."
    )
    parser.add_argument(
        "output_file",
        help="Path for the destination Excel (.xlsx) file."
    )
    
    # 3. Parse the arguments provided by the user
    args = parser.parse_args()

    # 4. Run the conversion function with the parsed arguments
    json_to_excel_streaming(args.input_file, args.output_file)

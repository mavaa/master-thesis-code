import json
import os
import requests
from src.util import create_folder_if_not_exists

def download_json(url, local_path):
    response = requests.get(url)
    response.raise_for_status()  # Check if the request was successful
    with open(local_path, 'w') as file:
        json.dump(response.json(), file)

def extract_source(json_file_path, sources_path):


    with open(json_file_path, 'r') as file:
        data = json.load(file)

    for task in data:
        if task['type'] == "O0":
            task_id = task['task_id']
            c_func = task['c_func']

            formatted_task_id = f"{task_id:03d}"

            filename = f"{sources_path}/task_{formatted_task_id}.c"

            with open(filename, 'w') as c_file:
                c_file.write(c_func)

            print(f"Saved {filename}")

base_path = 'data_decompile_eval'
sources_path = os.path.join(base_path, "sources")

# LLM4Decompile decompile-eval test dataset
json_url = 'https://raw.githubusercontent.com/albertan017/LLM4Decompile/main/decompile-eval/decompile-eval.json'
json_file_path = os.path.join(base_path, 'decompile-eval.json')

create_folder_if_not_exists(base_path)
create_folder_if_not_exists(sources_path)

download_json(json_url, json_file_path)
extract_source(json_file_path, sources_path)

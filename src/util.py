import os

def create_folder_if_not_exists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)

def read_whole_file(file_path):
    with open(file_path, 'r') as file:
        code = file.read()
    return code


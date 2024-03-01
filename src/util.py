import os

def create_folder_if_not_exists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)


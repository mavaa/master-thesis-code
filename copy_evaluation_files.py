import os
import shutil
import sys

def copy_evaluation_files(src_folder_name):
    # Define the paths
    dir1 = os.path.dirname(os.path.abspath(__file__))
    dir2 = os.path.join(dir1, '../report/')

    src_folder = os.path.join(dir1, 'out', src_folder_name, 'evaluation')
    dest_folder = os.path.join(dir2, 'pipeline_output', src_folder_name)

    # Check if source folder exists
    if not os.path.exists(src_folder):
        print(f"Source folder '{src_folder}' does not exist.")
        return

    # Check if destination folder exists, create if not
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
        print(f"Made folder: {dest_folder}")

    # Copy files from source to destination
    for filename in os.listdir(src_folder):
        src_file = os.path.join(src_folder, filename)
        dest_file = os.path.join(dest_folder, filename)
        shutil.copy(src_file, dest_file)
        print(f"Copied\n'{src_file}' to\n'{dest_file}'")

    print("All files copied successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <folder_name>")
    else:
        folder_name = sys.argv[1]
        copy_evaluation_files(folder_name)

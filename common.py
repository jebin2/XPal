from pathlib import Path
import os
import shutil
import string
from datetime import datetime, timedelta
from custom_logger import logger_config
import secrets
import hashlib
import random
import subprocess

def path_exists(path):
    return file_exists(path) or dir_exists(path)

def file_exists(file_path):
    try:
        return Path(file_path).is_file()
    except:
        pass
    return False

def dir_exists(file_path):
    try:
        return Path(file_path).is_dir()
    except:
        pass
    return False

def list_files_recursive(directory):
    # Initialize an empty array to store the file paths
    file_list = []
    
    # Walk through the directory recursively
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Get the full path of the file and append to the array
            file_list.append(os.path.join(root, file))
    
    return file_list

def list_directories_recursive(directory):
    # Initialize an empty list to store the directory names
    directory_list = []
    
    # Walk through the directory recursively
    for root, dirs, files in os.walk(directory):
        for dir_name in dirs:
            # Get the full path of the directory and append to the list
            directory_list.append(os.path.join(root, dir_name))
    
    return directory_list

def list_files(directory):
    # Initialize an empty array to store the file paths
    file_list = []
    
    # Get the list of files in the given directory (non-recursive)
    for file in os.listdir(directory):
        # Construct the full path and check if it's a file
        full_path = os.path.join(directory, file)
        if os.path.isfile(full_path):
            file_list.append(full_path)
    
    return file_list

def remove_path(path):
    remove_file(path, True)
    remove_all_files_and_dirs(path)

def remove_file(file_path, retry=True):
    try:
        # Check if the file exists
        if os.path.exists(file_path):
            # Remove the file
            os.remove(file_path)
            os.system(f"rm -f {file_path}")
            logger_config.success(f"{file_path} has been removed successfully.")
        else:
            logger_config.debug(f"{file_path} does not exist.")
    except Exception as e:
        logger_config.warning(f"Error occurred while trying to remove the file: {e}")
        if retry:
            logger_config.debug("retrying after 10 seconds", seconds=10)
            remove_file(file_path, False)

def remove_all_files_and_dirs(directory):
    try:
        shutil.rmtree(directory)  # Recursively delete a directory
    except Exception as e:
        logger_config.warning(f"Failed to delete {directory}. Reason: {e}")

def remove_directory(directory_path):
    try:
        if os.path.exists(directory_path):
            shutil.rmtree(directory_path)
            logger_config.debug(f'Directory Deleted at: {directory_path}')
    except Exception as e:
        logger_config.warning(f'An error occurred: {e}')

def create_directory(directory_path):
    try:
        # Create the directory
        os.makedirs(directory_path, exist_ok=True)  # exist_ok=True avoids error if the dir already exists
        logger_config.debug(f'Directory created at: {directory_path}')
    except Exception as e:
        logger_config.error(f'An error occurred: {e}')

def generate_random_string(length=10):
    characters = string.ascii_letters
    random_string = ''.join(secrets.choice(characters) for _ in range(length))
    return random_string

def get_date(when=0):
    today = datetime.now()
    sub_day = today - timedelta(days=when)

    sub_day_str = sub_day.strftime('%Y-%m-%d')    
    return sub_day_str

def generate_random_string_from_input(input_string, length=10):
    # Hash the input string to get a consistent value
    hash_object = hashlib.md5(input_string.encode())
    hashed_string = hash_object.hexdigest()

    # Use the hash to seed the random number generator
    random.seed(hashed_string)

    # Generate a random string based on the seed
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))

    return random_string

def rename_file(current_name, new_name):
    try:
        # Rename the file
        os.rename(current_name, new_name)
        print(f"File renamed from '{current_name}' to '{new_name}'")
    except FileNotFoundError:
        print(f"The file '{current_name}' was not found.")
    except FileExistsError:
        print(f"A file named '{new_name}' already exists.")
    except Exception as e:
        print(f"An error occurred: {e}")

def copy(source, dest):
    try:
        subprocess.run(["cp", source, dest], check=True)
    except Exception as e:
        print(f"An error occurred: {e}")
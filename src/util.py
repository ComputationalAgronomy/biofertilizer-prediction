import glob
import os
import re
import time

def create_folder(abs_dir, foldername, foldernum=1):
    """This function will create a folder if the folder name specified
       doesn't exist"""
    folder_path = os.path.join(abs_dir, foldername)
    while os.path.exists(folder_path):
        if foldernum > 100:
            raise Exception("A bug in creating a folder!")
        foldernum += 1
        foldername = re.sub("_(\d+)$", f"_{str(foldernum)}", foldername)
        folder_path = os.path.join(abs_dir, foldername)
    os.makedirs(folder_path)  
    
    return foldername

# [directory_name]/[filename].csv
def create_savename_serial(abs_dir, filename, filenum=1, new_folder=True, no_create=False):
    """This function will create a proper filename for the output file"""   
    filename = os.path.basename(filename)
    filename = re.search("(.*)\.", filename).group(1)
    if no_create:
        foldername = "output"
        if not os.path.exists(os.path.join(abs_dir, foldername)):
            os.makedirs(foldername)
    else:    
        foldername = "output_1"
        if new_folder:
            foldername = create_folder(abs_dir, foldername)
    filename = os.path.join(abs_dir,
                            foldername,
                            f"{filename}.csv")
   
    return filename

def create_savename(output_path, filename, save_format):
    basename_old_extension = os.path.basename(filename)
    basename = basename_old_extension.rsplit(".", 1)[0]
    basename_new_extension = f"{basename}.{save_format}"
    output_name = os.path.join(output_path, basename_new_extension)
    return output_name

def make_dir(path):
    try:
        os.makedirs(path)
    except FileExistsError:
        pass

def find_file(input_path, pattern):
    file_list = glob.glob(os.path.join(input_path, pattern), recursive=True)
    file_list = [file.replace("\\", "/") for file in file_list]
    return file_list

def check_files_in_path(input_path, pattern):
    if os.path.isdir(input_path):
        file_list = find_file(input_path, pattern)
    elif os.path.isfile(input_path):
        file_list = input_path
    return file_list

def timer(func):
    def inner_func(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__}: {round(end - start, 2)}sec")
    return inner_func

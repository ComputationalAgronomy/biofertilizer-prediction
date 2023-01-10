import glob
import os
import statistics as st
import sys

import pandas as pd
from tqdm import tqdm

result_list = []
total_compound_dict = {}
total_enzyme_dict = {}

class Result():
    
    def __init__(self, filename):
        self.get_name(filename)
        self.compound_dict = {}
        self.enzyme_dict = {}
        self.parse_result(filename)
    
    def get_name(self, filename):
        self.name = os.path.basename(filename)

    def parse_result(self, filename):
        count_compound, count_enzyme = False, False
        with open(filename, "r") as f:
            for line in f.readlines():
                line = line.strip("\n")
                if line == "Compound list:":
                    count_compound, count_enzyme = True, False
                    continue
                elif line == "Enzyme list:":
                    count_compound, count_enzyme = False, True
                    continue
                elif line == "":
                    continue
                else:
                    if count_compound:
                        compound_id, compound_score = line.split(":")[0:2]
                        compound_score = float(compound_score)
                        self.compound_dict[compound_id] = compound_score
                        try:
                            total_compound_dict[compound_id].append(compound_score)
                        except KeyError:
                            total_compound_dict[compound_id] = [compound_score]
                    elif count_enzyme:
                        enzyme_id, enzyme_score = line.split(":")[0:2]
                        enzyme_score = float(enzyme_score)
                        self.enzyme_dict[enzyme_id] = enzyme_score
                        try:
                            total_enzyme_dict[enzyme_id].append(enzyme_score)
                        except KeyError:
                            total_enzyme_dict[enzyme_id] = [enzyme_score]


def write_output(dict, type, output_path):
    with open(os.path.join(output_path, f"{type}_output.csv"), "w") as f:
        f.writelines(f"{type}_key,{type}_value,max,min,mean,stdev\n")
        for key, value in dict.items():
            f.writelines(f"{key},{sum(value)},{max(value)},"
                         f"{min(value)},{st.mean(value)},{st.stdev(value)}\n")


def write_prediction(result_list, output_path):
    with open(os.path.join(output_path, f"prediction_output.csv"), "w") as f:
        f.writelines(f"species,score\n")
        for obj in result_list:
            species = obj.name.rsplit(".", 1)[0]
            score = obj.compound_dict["iaa"]
            f.writelines(f"{species},{score}\n")


def enzyme_mapping_analysis(path, output_path):
    if os.path.isdir(path):
        file_list = glob.glob(os.path.join(path, "**/*.txt"), recursive=True)
        file_list = [file.replace("\\", "/") for file in file_list]
        for filename in tqdm(file_list):
            result_list.append(Result(filename))
        write_output(total_compound_dict, "compound", output_path)
        write_output(total_enzyme_dict, "enzyme", output_path)
        result_list.sort(key=lambda obj: obj.compound_dict["iaa"], reverse=True)
        write_prediction(result_list, output_path)
    else:
        print("Invalid directory name")
        sys.exit()


if __name__ == "__main__":
    # python file path
    path = sys.argv[1]
    output_path = os.path.dirname(__file__)
    enzyme_mapping_analysis(path, output_path)

import argparse
import glob
import logging
import os
import time
from datetime import datetime

import tomli
from tqdm import tqdm

from biopathpred.modules.best_blast import find_best_blast
from biopathpred.modules.match_enzyme import start_match_enzyme
from biopathpred.modules.parse_ncbi_xml import parse_blast
from biopathpred.modules.run_scripts import run_blast, run_prodigal
from typing import Literal

ROOT_DIR = os.path.dirname(__file__)

class Configuration():
    """Configure input and output path, and check parameters.

    Attributes:
        args: The given argparse `Namespace` object for storing command-line arguments.
        type: A single module or whole pipeline to be run.
    """
    def __init__(self, args):
        """Initialize the instance based on argparse inputs.

        Args:
            args: Parsed arguments of argparse.
        """
        self.args = args
        self.type = args.type
        self._is_module = False if self.type == "main" else True
        self._file_ext_dict = {"parse_blast": {"input": "xml", "output": "csv"},
                               "best_blast": {"input": "csv", "output": "csv"},
                               "match_enzyme": {"input": "csv", "output": "txt"}}
        self._load_default_config()
        self._config_logging()

    def check_io(self, type: Literal["parse_blast", "best_blast", "match_enzyme"]):
        """Determine the input and output path for each module.
        
        Args:
            type: 
        """
        # If "True" means we pipeline the results from the previous step, so
        # self.type has not yet been changed.
        if type != self.type and self.type != "main":
            try:
                self.base_path
            except AttributeError:
                self.get_base_path()
            self.input_path = self.output_path
        else:
            self.input_path = os.path.normpath(self.args.input)
            self.get_base_path()
        self.output_path = os.path.join(self.base_path, type)
        self.type = type

        # prodigal and blast scripts will handle this part
        # check input filetype
        try:
            self._file_ext_dict[type]
            self.file_list = self.check_files_in_path()
            os.makedirs(self.output_path, exist_ok=True)
        except KeyError:
            pass

        # check extra param
        self.check_param()

    def _load_default_config(self):
        with open(os.path.join(ROOT_DIR, "config.toml"), "rb") as f:
            self.default = tomli.load(f)

    def check_param(self):
        if self.type == "parse_blast":
            self.database = self.args.database
            if self.database is None:
                database_path = self.default["database"]["path"]
            self.database = os.path.normpath(database_path)
            self.check_blast_database(self.database)
        elif self.type == "best_blast":
            self.criteria = self.args.criteria
            if self.criteria is None:
                self.criteria = self.default["criteria"]["column"]
            self.filter = self.args.filter
            if self.filter is None:
                self.filter = self.default["criteria"]["filter"]
        elif self.type == "match_enzyme":
            self.model = self.args.model
            if self.model is None:
                self.model = self.default["match_enzyme"]["model"]

    def get_base_path(self):
        try:
            self.base_path = os.path.normpath(os.path.abspath(self.args.output))
        except TypeError:
            if self._is_module:
                self.base_path = os.path.join(ROOT_DIR, "module_output")
            else:
                self.base_path = os.path.join(ROOT_DIR, "tmp")

    def create_savename(self, filename):
        filetype = self._file_ext_dict[self.type]["output"]
        basename = os.path.basename(filename)
        basename_no_extension = basename.rsplit(".", 1)[0]
        savename_no_extension = os.path.join(self.output_path, basename_no_extension)
        savename_new_extension = f"{savename_no_extension}.{filetype}"
        return savename_new_extension

    def check_files_in_path(self):
        input_path = self.input_path
        if os.path.isdir(input_path):
            filetype = self._file_ext_dict[self.type]["input"]
            pattern = f"*.{filetype}"
            file_list = Configuration.find_file(input_path, pattern)
        elif os.path.isfile(input_path):
            file_list = [input_path]
        return file_list

    def _config_logging(self):
        now = datetime.now().strftime("%y%m%d%H%M%S")
        logger = logging.getLogger("pipeline_log")
        logger.setLevel(logging.INFO)

        sh = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s\t[%(levelname)s]\t%(message)s",
                                    "%Y-%m-%d %H:%M:%S")
        sh.setFormatter(formatter)
        logger.addHandler(sh)

        try:
            logging_path = os.path.join(self.args.output, f"log_{now}.txt")
            os.makedirs(self.args.output, exist_ok=True)
        except TypeError:
            logging_path = os.path.join(ROOT_DIR)

        fh = logging.FileHandler(logging_path)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        self.logger = logger

    @staticmethod
    def find_file(input_path, pattern):
        file_list = glob.glob(os.path.join(input_path, pattern), recursive=True)
        return file_list

    def check_blast_database(self, database_path):
        self.logger.info("Check blast database existence")
        if os.path.isfile(database_path):
            self.logger.info(f"Database: {os.path.basename(database_path)}")
        else:
            raise Exception("Blast database does not exist. Check config.toml before running.")



# run individual modules
def run_parse_blast(config: Configuration):
    config.check_io(type="parse_blast")
    config.logger.info("Parse blastp result")
    for filename in config.file_list:
        savename = config.create_savename(filename)
        parse_blast(filename=filename, output_filename=savename)
    config.logger.info("Done!")


def run_find_best_blast(config: Configuration):
    config.check_io(type="best_blast")
    config.logger.info("Select the best blastp result based on the configuration")
    for filename in config.file_list:
        savename = config.create_savename(filename)
        find_best_blast(filename=filename, output_filename=savename,
                        criteria=config.criteria, filter=config.filter)
    config.logger.info("Done!")


def run_match_enzyme(config: Configuration):
    config.check_io("match_enzyme")
    config.logger.info("Match the best blastp result to the pathway")
    for filename in config.file_list:
        savename = config.create_savename(filename)
        start_match_enzyme(filename=filename, output_filename=savename,
                        model=config.model, quiet=config.args.quiet)
    config.logger.info("Done!")


def parent_arguments():
    parent_parser = argparse.ArgumentParser(description="Parent parser.",
                                            add_help=False)
    parent_parser.add_argument("-i", "--input", type=str, required=True,
                               help="input a file or directory path")
    parent_parser.add_argument("-o", "--output", type=str, help="output path")

    return parent_parser


def optional_arguments(case="main"):
    optional_parser = argparse.ArgumentParser(description="Optional parser.",
                                              add_help=False)
    if case == "main":
        optional_parser.add_argument("-i", "--input", type=str, required=False,
                                     help="input a file or directory path")
        optional_parser.add_argument(
            "-db", "--database", type=str, help="database path")
        optional_parser.add_argument(
            "-c", "--criteria", type=str, help="selection criteria")
        optional_parser.add_argument(
            "-f", "--filter", nargs="*", type=str, help="filter options")
        optional_parser.add_argument(
            "-m", "--model", type=str, help="model name")
        optional_parser.add_argument("--quiet", action="store_true",
                                     help="do not print result to screen")
        # --debug not yet implemented
        optional_parser.add_argument("--debug", action="store_true",
                                     help="keep tmp folder if specified")
    elif case == "blast":
        optional_parser.add_argument(
            "-db", "--database", type=str, help="database path")
    elif case == "best_blast":
        optional_parser.add_argument(
            "-c", "--criteria", type=str, help="selection criteria")
        optional_parser.add_argument(
            "-f", "--filter", nargs="*", type=str, help="filter options")
    elif case == "match_enzyme":
        optional_parser.add_argument("param_start", type=int)
        optional_parser.add_argument("param_end", type=int)
        optional_parser.add_argument(
            "-m", "--model", type=str, help="model name")
        optional_parser.add_argument("--quiet", action="store_true",
                                     help="do not print result to screen")
    else:
        pass

    return optional_parser


def parse_arguments():
    parser = argparse.ArgumentParser(parents=[parent_arguments(),
                                              optional_arguments()],
                                     conflict_handler='resolve')
    parser.set_defaults(func=main, type="main")

    # with subcommand: run individual module
    subparser = parser.add_subparsers(help="module name")
    prodigal_parser = subparser.add_parser(
        "prodigal",
        parents=[parent_arguments(), optional_arguments(case="prodigal")],
        conflict_handler='resolve')
    prodigal_parser.set_defaults(func=run_prodigal, type="prodigal")

    blast_parser = subparser.add_parser(
        "blastp",
        parents=[parent_arguments(), optional_arguments(case="blast")],
        conflict_handler='resolve')
    blast_parser.set_defaults(func=run_blast, type="blast")

    xml_parser = subparser.add_parser(
        "parse_xml",
        parents=[parent_arguments(), optional_arguments(case="parse_xml")],
        conflict_handler='resolve')
    xml_parser.set_defaults(func=run_parse_blast, type="parse_blast")

    best_blast_parser = subparser.add_parser(
        "best_blast",
        parents=[parent_arguments(), optional_arguments(case="best_blast")],
        conflict_handler='resolve')
    best_blast_parser.set_defaults(func=run_find_best_blast, type="best_blast")

    match_enzyme_parser = subparser.add_parser(
        "match_enzyme",
        parents=[parent_arguments(), optional_arguments(case="match_enzyme")],
        conflict_handler='resolve')
    match_enzyme_parser.set_defaults(
        func=run_match_enzyme, type="match_enzyme")

    args = parser.parse_args()

    return args


def main(config: Configuration):
    # count total execution time
    time_start = time.time()

    # scripts
    # run prodigal gene prediction
    run_prodigal(config)
    # run blastp protein alignment
    run_blast(config)

    # python functions
    # parse_blast
    run_parse_blast(config)

    # find_best_blast
    # criteria default: find highest bit-score (column: score)
    # options: score, evalue, identity_percentage, query_coverage
    run_find_best_blast(config)

    # match_enzyme
    run_match_enzyme(config)

    time_end = time.time()
    config.logger.info(f"Elapsed time: {round(time_end - time_start, 2)}sec")




if __name__ == "__main__":
    args = parse_arguments()
    config = Configuration(args)
    args.func(config)


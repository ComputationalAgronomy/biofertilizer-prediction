import pandas as pd
from .util import *


def find_best_blast(filename, output, criteria="score"):
    file = pd.read_csv(filename)
    # filter the best result in each group (gene_prediction_id)
    data = file.loc[file.groupby(["id"])[criteria].idxmax()]
    data.to_csv(output, index=False)

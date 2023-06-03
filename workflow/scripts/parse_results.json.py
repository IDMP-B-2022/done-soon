import matplotlib.pyplot as plt
import json
import logging
from argparse import ArgumentParser
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level="NOTSET", format="%(message)s", datefmt="[%X]"
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def parse_files(files):
    # Initialize an empty DataFrame to store the results
    results = []

    # Iterate over each file in the directory
    for file in files:
        data = json.loads(file.read_text())
        # Extract the required values from the JSON data
        std = data["std"]
        maximum = data["maximum"]
        average = data["average"]
        original_target = data["original_target"]

        # Append the values to the DataFrame
        results_dict = {
            "std": std,
            "maximum": maximum,
            "average": average,
        }

        original_dict = json.loads(Path(original_target).read_text())
        results_dict = {**results_dict, **original_dict}

        # Append the dictionary to the list
        results.append(results_dict)

    # Create a DataFrame from the list of dictionaries
    results_df = pd.DataFrame(results)

    return results_df


def model_selection(dataframe):
    pass


def main():
    """
    Script to convert the problem output json files to a pickle of a
    dictionary of features at each percentage of the time limit.
    """
    parser = ArgumentParser(description="Cross validate a target dataset")
    parser.add_argument(
        "outputs",
        type=str,
        help="Path to JSON file directory containing outputs of crossvalidation",
    )

    args = parser.parse_args()

    target_dir_path = Path(args.outputs)

    dataframe = parse_files(target_dir_path.glob("*.json"))
    model_selection(dataframe)


if __name__ == "__main__":
    main()


import pickle
from argparse import ArgumentParser
from pathlib import Path

from sklearn.model_selection import train_test_split
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def split_into_train_and_test(features_at_percent, random_state):
    train_at_percentage = {}
    test_at_percentage = {}

    for percentage in range(1, 41):
        labels = features_at_percent[percentage]['solved_within_time_limit']
        train, test = train_test_split(features_at_percent[percentage], test_size=0.1, random_state=random_state, stratify=labels)
        train_at_percentage[percentage] = train
        test_at_percentage[percentage] = test

    return train_at_percentage, test_at_percentage


def main():
    """
    Script to split the features into train set for base experiment.
    """
    parser = ArgumentParser(description="Convert output json files to features at percent")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Pickle containing the features at percent",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Base filename of train set splits",
    )
    parser.add_argument(
        "--random",
        type=int,
        default=5,
        help="The seed for the random number generator",
    )

    args = parser.parse_args()

    input_features_path = Path(args.input)
    output_filename = args.output
    output_dir = Path(args.output).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Created output directory {output_dir}")

    with open(input_features_path, "rb") as f:
        features_at_percent = pickle.load(f)

    train, test = split_into_train_and_test(features_at_percent, random_state=args.random)

    with open(f"{output_filename}_train.pkl", "wb") as f:
        pickle.dump(train, f)

    with open(f"{output_filename}_test.pkl", "wb") as f:
        pickle.dump(test, f)

    logger.info(f"Saved features at percent dict to {output_filename}")


if __name__ == "__main__":
    main()

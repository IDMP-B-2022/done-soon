import json
import logging
import pickle
import sys
from argparse import ArgumentParser
from glob import glob
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.dummy import DummyClassifier

logging.basicConfig(
    level="NOTSET", format="%(message)s", datefmt="[%X]"
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_models():
    models = {'LR': LogisticRegression(max_iter=1000, C=1000, class_weight='balanced', random_state=22),
              'SVM': SVC(kernel='rbf', class_weight='balanced', probability=True, random_state=22),
              'RF': RandomForestClassifier(min_samples_leaf=5, class_weight='balanced_subsample', random_state=22),
              'ET': ExtraTreesClassifier(class_weight='balanced', random_state=22),
              'MLP': MLPClassifier(random_state=22), 'AB': AdaBoostClassifier(),
              'DT': DecisionTreeClassifier(max_depth=5, class_weight='balanced', random_state=22),
              'DUM': DummyClassifier(strategy="stratified")}
    return models


def cross_validate(target, features_at_percent):
    


def main():
    """
    Script to convert the problem output json files to a pickle of a
    dictionary of features at each percentage of the time limit.
    """
    parser = ArgumentParser(description="Cross validate a target dataset")
    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="Path to JSON file containing a target for cross validation",
    )
    parser.add_argument(
        "--pickle",
        type=str,
        required=True,
        help="Path to features at percentage pickle",
    )
    parser.add_argument(
        "--output",
        type=int,
        default=1,
        help="Path to output directory",
    )

    args = parser.parse_args()

    target_path = Path(args.target)
    features_at_percent_path = Path(args.pickle)
    output_path = Path(args.output)

    output_path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Created output directory {output_dir}")

    # Load the problem output json files into a dataframe
    target = json.loads(target_path.read_text())

    # Create features at each percentage of the time limit
    features_at_percent = pickle.loads(features_at_percent_path.read_bytes())
    logger.info("Loaded features at percent pickle")

    cross_validate(target, features_at_percent)


if __name__ == "__main__":
    main()

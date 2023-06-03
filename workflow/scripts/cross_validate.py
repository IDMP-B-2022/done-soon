import json
import logging
import pickle
from argparse import ArgumentParser
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import MaxAbsScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

logging.basicConfig(
    level="NOTSET", format="%(message)s", datefmt="[%X]"
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_model(model):
    models = {'LR': LogisticRegression(max_iter=1000, C=1000, class_weight='balanced'),
              'SVM': SVC(kernel='rbf', class_weight='balanced', probability=True),
              'RF': RandomForestClassifier(min_samples_leaf=5, class_weight='balanced_subsample'),
              'ET': ExtraTreesClassifier(class_weight='balanced'),
              'MLP': MLPClassifier(),
              'AdaBoost': AdaBoostClassifier(),
              'DT': DecisionTreeClassifier(max_depth=5, class_weight='balanced'),
              'DUM': DummyClassifier(strategy="stratified")}
    return models[model]


def preprocessing(dataframe, target):
    result = dataframe.drop(['mzn', 'dzn'], axis=1)
    if target['preprocessing']['drop_constant_values']:
        result.drop(result.columns[result.nunique() == 1], axis=1, inplace=True)  # drop cols with constant value

    if target['preprocessing']['scale']:
        transformer = MaxAbsScaler().fit(result)
        result = pd.DataFrame(transformer.transform(result), columns=result.columns,
                              index=result.index)  # normalise data
    return result


def cross_validate(target, features_at_percent):
    percentage = target['percentage']
    data_at_percentage: pd.DataFrame = features_at_percent[percentage]

    if not target['use_ewma']:
        data_at_percentage = data_at_percentage[
            data_at_percentage.columns[~data_at_percentage.columns.str.contains("ewma")]
        ]

    if not target['use_gradient']:
        data_at_percentage = data_at_percentage[
            data_at_percentage.columns[~data_at_percentage.columns.str.contains("gradient")]
        ]

    model = create_model(target['model'])

    data_at_percentage = preprocessing(data_at_percentage, target)

    # K-fold
    stratified_k_fold = StratifiedKFold(n_splits=target['k_fold']['n_splits'], shuffle=True)

    f1_scores = []

    for train, test in stratified_k_fold.split(
            data_at_percentage.drop(columns=["solved_within_time_limit"]),
            data_at_percentage["solved_within_time_limit"]):
        train_data = data_at_percentage.iloc[train]
        test_data = data_at_percentage.iloc[test]

        train_x, train_y = train_data.drop(columns=["solved_within_time_limit"]), train_data["solved_within_time_limit"]
        test_x, test_y = test_data.drop(columns=["solved_within_time_limit"]), test_data["solved_within_time_limit"]
        model = model.fit(train_x, train_y)

        predictions = model.predict(test_x)

        current_f1_score = f1_score(test_y, predictions)
        f1_scores.append(current_f1_score)

    return {
        'f1_scores': f1_scores,
        'std': np.std(f1_scores),
        'maximum': max(f1_scores),
        'average': np.average(f1_scores)
    }


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
        type=str,
        help="Path to output directory",
    )

    args = parser.parse_args()

    target_path = Path(args.target)
    features_at_percent_path = Path(args.pickle)
    output_path = Path(args.output)

    output_path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Created output directory {output_path}")

    # Load the problem output json files into a dataframe
    target = json.loads(target_path.read_text())

    # Create features at each percentage of the time limit
    features_at_percent = pickle.loads(features_at_percent_path.read_bytes())
    logger.info("Loaded features at percent pickle")

    cross_validate(target, features_at_percent)


if __name__ == "__main__":
    main()

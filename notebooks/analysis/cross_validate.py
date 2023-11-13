import collections
import json
import logging
import multiprocessing
import pickle
from argparse import ArgumentParser
from pathlib import Path

import functools
import pandas as pd
from rich import progress
from rich.logging import RichHandler
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

def warn(*args, **kwargs):
    pass

# hide sklearn warnings about lack of convergence
import warnings
warnings.warn = warn

# logging.basicConfig(
    # level="NOTSET", format="%(message)s", datefmt="[%X]"
# )
FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET",
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


def create_model(model, hyperparameters):
    if model == 'LR':
        return LogisticRegression(**hyperparameters, class_weight='balanced')
    elif model == 'SVM':
        return SVC(**hyperparameters, class_weight='balanced', probability=True)
    elif model == 'RF':
        return RandomForestClassifier(**hyperparameters, class_weight='balanced_subsample')
    elif model == 'ET':
        return ExtraTreesClassifier(**hyperparameters, class_weight='balanced')
    elif model == 'MLP':
        return MLPClassifier(**hyperparameters)
    elif model == 'AdaBoost':
        return AdaBoostClassifier(**hyperparameters)
    elif model == 'DT':
        return DecisionTreeClassifier(**hyperparameters, class_weight='balanced')
    elif model == 'DUM':
        return DummyClassifier(**hyperparameters, strategy="stratified")
    else:
        raise ValueError(f"Unsupported model: {model}")


def preprocessing(dataframe, target):
    result, mzn = dataframe.drop(columns=["mzn", 'dzn'], axis=1), dataframe["mzn"]

    if 'has_gradients' in result.columns:
        result.drop(['has_gradients'], axis=1)
    if target['preprocessing']['drop_constant_values']:
        result.drop(result.columns[result.nunique() == 1], axis=1, inplace=True)  # drop cols with constant value
    if len(dataframe) == 0:
        raise ValueError("No more points for current percentage.")

    if target['preprocessing']['scale']:
        transformer = MaxAbsScaler().fit(result)
        result = pd.DataFrame(transformer.transform(result), columns=result.columns,
                              index=result.index)  # normalise data

    result['mzn'] = mzn

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

    if target['use_gradient']:
        if 'has_gradients' in data_at_percentage.columns:
            data_at_percentage = data_at_percentage[data_at_percentage['has_gradients']]

    data_at_percentage = preprocessing(data_at_percentage, target)

    model = create_model(target['model'], target['hyperparameters'])
    # K-fold
    stratified_k_fold = StratifiedKFold(n_splits=target['k_fold']['n_splits'], shuffle=True)

    f1_scores = []
    f1_scores_per_problem = collections.defaultdict(list)

    for train, test in stratified_k_fold.split(
            data_at_percentage.drop(columns=["solved_within_time_limit"]),
            data_at_percentage["solved_within_time_limit"]):
        train_data = data_at_percentage.iloc[train]
        test_data = data_at_percentage.iloc[test]

        train_x, train_y = train_data.drop(columns=["solved_within_time_limit"]), train_data["solved_within_time_limit"]
        test_x, test_y = test_data.drop(columns=["solved_within_time_limit"]), test_data["solved_within_time_limit"]

        train_x = train_x.drop(['mzn'], axis=1)
        model = model.fit(train_x, train_y)

        test_x, mzn = test_x.drop(["mzn"], axis=1), test_x["mzn"]
        predictions = model.predict(test_x)
        current_f1_score = f1_score(test_y, predictions)
        f1_scores.append(current_f1_score)

        test_x['mzn'] = mzn
        test_x['gt'] = test_y
        test_x['predictions'] = predictions
        for problem in set(test_x['mzn'].values):
            data_for_problem = test_x[test_x['mzn'] == problem]
            amount_of_points = len(data_for_problem)

            gt, predictions = data_for_problem['gt'], data_for_problem['predictions']

            vc = ((gt == predictions).value_counts(normalize=True).to_dict())

            correct = 0 if True not in vc else vc[True]

            f1_scores_per_problem[problem].append({

                'length': amount_of_points,
                'percentage': percentage,
                'correct': correct

            })

    return model, dict(hyperparameters=target['hyperparameters'],
                       f1_scores=f1_scores,
                       per_problem=dict(f1_scores_per_problem))


def run_per_target(target_path, output_path, features_at_percent):
    if output_path.joinpath(target_path.stem).with_suffix(".json").exists():
        logger.info(f"{output_path.joinpath(target_path.stem).with_suffix('.json')} exists. Skipping.")
        return


    logger.info(f"Loading {target_path}")
    target = json.loads(target_path.read_text())
    try:
        model, result = cross_validate(target, features_at_percent)
        result['original_target'] = str(target_path)
    except ValueError as e:
        logger.error(f"Error: {e}")
        return

    model_path = output_path.joinpath(target_path.stem).joinpath("./model").with_suffix(".pkl")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    result_path = output_path.joinpath(target_path.stem).joinpath("./data").with_suffix(".json")
    result_path.parent.mkdir(parents=True, exist_ok=True)

    result['model_path'] = str(model_path)

    with model_path.open('wb') as f:
        pickle.dump(model, f)

    result_path.write_text(json.dumps(result))

    logger.info(f"Logged output to {str(result_path)}")

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
        help="Path to JSON file directory containing targets for cross validation",
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

    target_dir_path = Path(args.target)
    features_at_percent_path = Path(args.pickle)
    output_path = Path(args.output)

    output_path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Created output directory {output_path}")

    features_at_percent: dict[int, pd.DataFrame] = pickle.loads(features_at_percent_path.read_bytes())

    targets = list(target_dir_path.glob("*.json"))

    with multiprocessing.Pool() as pool:
        with progress.Progress(expand=True) as pbar:
            task = pbar.add_task("[red]Cross validating...", total=len(targets))
            for _ in pool.imap(functools.partial(
                    run_per_target,
                    output_path=output_path,
                    features_at_percent=features_at_percent
            ), targets):
                pbar.advance(task)


if __name__ == "__main__":
    main()

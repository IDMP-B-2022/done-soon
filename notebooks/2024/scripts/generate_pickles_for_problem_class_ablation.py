import pickle
from argparse import ArgumentParser

from pathlib import Path
from typing import List
import random



def size_for_set_of_labels(problem_with_counts: dict[str, int], problems: list[str]):
    return sum(problem_with_counts[i] for i in problems)

def knapsack(problem_with_counts: dict[str, int], percentage_split=0.2, random_state=42) -> List[str]:
    """
    Takes a set of unique problems (by mzn) and returns a subset of unique problems
    that approximate a % split. Allows to set a random state in order to randomize datasets.
    """
    random.seed(random_state)
    stack = []
    total_length = sum(problem_with_counts.values())
    size_for_set_of_labels = 0

    # Loop until target size is reached or all problems are considered
    while size_for_set_of_labels < percentage_split * total_length and problem_with_counts:
        # Randomly choose the next problem (weighted by count)
        next_choice = random.choices(list(problem_with_counts.keys()), k=1)

        # Add chosen problem to stack (ensuring uniqueness)
        if next_choice[0] not in stack:
            stack.append(next_choice[0])
            size_for_set_of_labels += problem_with_counts[next_choice[0]]
            del problem_with_counts[next_choice[0]]  # Remove processed problem

    return stack

def split_into_train_and_test(features_at_percent, random_state):
    train_at_percentage = {}
    test_at_percentage = {}

    for percentage in range(1, 41):
        model_counts: dict[str, int] = features_at_percent[percentage]['mzn'].value_counts().to_dict()
        print(model_counts)
        
        percentage_subset_of_problems = knapsack(model_counts, percentage_split=0.2, random_state=random_state)

        train_at_percentage[percentage] = features_at_percent[percentage][~features_at_percent[percentage]['mzn'].isin(percentage_subset_of_problems)]
        test_at_percentage[percentage] = features_at_percent[percentage][features_at_percent[percentage]['mzn'].isin(percentage_subset_of_problems)]

        print(train_at_percentage[percentage].columns[train_at_percentage[percentage].isna().any()].tolist())

    return train_at_percentage, test_at_percentage


def main():
    """
    Script to split the features into train set for the problem class ablation.
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

    with open(input_features_path, "rb") as f:
        features_at_percent = pickle.load(f)

    train, test = split_into_train_and_test(features_at_percent, random_state=args.random)

    with open(f"{output_filename}_train.pkl", "wb") as f:
        pickle.dump(train, f)

    with open(f"{output_filename}_test.pkl", "wb") as f:
        pickle.dump(test, f)


if __name__ == "__main__":
    main()
import json
import pickle
import sys
from argparse import ArgumentParser
from glob import glob
from pathlib import Path

import pandas as pd
from rich.progress import track
from rich.logging import RichHandler
from sklearn.model_selection import train_test_split
import logging

logging.basicConfig(
    level="NOTSET", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# find index of statistics array at certain percent of TL
def find_index_at_percent(stats, wall_clock_time_to_find):
    left = 0
    right = len(stats) - 1
    while left <= right:
        mid = (left + right) // 2

        if stats[mid] is not None:

            if abs(left - right) <= 1:
                left_time_at_convergence = stats[left]['search_time']
                right_time_at_convergence = stats[right]['search_time']

                left_difference = abs(wall_clock_time_to_find - left_time_at_convergence)
                right_difference = abs(wall_clock_time_to_find - right_time_at_convergence)

                if left_difference < right_difference:
                    value = left_time_at_convergence
                    difference = left_difference
                    index_to_return = left
                else:
                    value = right_time_at_convergence
                    difference = right_difference
                    index_to_return = right

                if difference > 72:
                    return -1
                return index_to_return

            elif stats[mid]['search_time'] < wall_clock_time_to_find:
                left = mid
            else:
                right = mid
        else:
            logger.warning("none? %d", mid)
            return -1

    logger.warning("%d never converges?", mid)
    return -1


def load_to_dataframe(input_dir: Path) -> pd.DataFrame:
    all_normal_files = glob(str(input_dir / "*NORMAL.json"))
    all_normal_files = list(all_normal_files)
    df = pd.DataFrame()
    data = []

    num_without_search_time = 0
    for i, normal in track(enumerate(all_normal_files), description="Loading data", total=len(all_normal_files),
                           transient=True):
        mzn = normal[normal.find("MZN-") + 4:normal.find("-DZN")] + ".mzn"
        dzn = normal[normal.find("DZN-") + 4:normal.find("-OUTPUT")] + ".dzn"

        stats = Path(f"{normal[:-12]}-STATS.json")
        if stats.exists():
            with open(normal, 'r') as normal_output, open(f"{normal[:-12]}-STATS.json", 'r') as stats_output:
                line = normal_output.readline()
                if line:  # don't read json from empty output

                    normal_time = json.loads(line).get('time')  # wall time
                    stats_all_lines = [json.loads(line).get('statistics') for line in stats_output.readlines()]
                    final_statistic = stats_all_lines[-1]

                    # plot_dataframe_column(pd.DataFrame(stats_all_lines), 'search_time')

                    if normal_time and final_statistic:
                        if "search_time" not in final_statistic.keys():
                            num_without_search_time += 1
                        else:
                            normal_time *= 0.001  # Convert from milliseconds to seconds

                            if normal_time <= 10:
                                continue

                            # To avoid loading in too much data into memory, only load the ones at certain percentages
                            # specifically, every half percent intervals
                            statistics_per_half_percent = {}
                            for percent in range(1, 200):

                                # normal_time is in seconds, so this is percentage of two hours
                                wall_clock_time_at_percent = (60 * 60 * 2) * percent / 100 / 2

                                if wall_clock_time_at_percent >= final_statistic['search_time']:  # no more data :(
                                    break

                                logger.debug("searching for", wall_clock_time_at_percent)

                                index_for_percent = find_index_at_percent(stats_all_lines, wall_clock_time_at_percent)
                                logger.debug(index_for_percent)

                                if index_for_percent == -1:
                                    statistics_per_half_percent[percent] = None

                                logger.debug(stats_all_lines[index_for_percent]['search_time'])

                                statistics_per_half_percent[percent] = stats_all_lines[index_for_percent]

                            data.append({
                                'normal_time': normal_time,
                                'stat_time': final_statistic['search_time'],
                                'problem': normal,
                                'statistics': statistics_per_half_percent,
                                'mzn': mzn,
                                'dzn': dzn
                            })

    df = pd.DataFrame(data)

    return df


def cleanup(df):
    if "decision_level_sat" in df:
        del df["decision_level_sat"]
    if "ewma_decision_level_mip" in df:
        del df["ewma_decision_level_mip"]
    if "decision_level_mip" in df:
        del df["decision_level_mip"]

    # Added
    del df["best_objective"]
    del df["ewma_best_objective"]

    #Previous equations:
    # df["unassnVar"]   = (2**df['vars']) - df['decisions']
    # df["fracFailUnassn"]     = df['conflicts'] / df['unassnVar']         # num failures/ num open nodes
    # df["fracOpenVisit"] = (df['vars'] - df['opennodes']) / (df['opennodes'] + sys.float_info.epsilon)  # ratio of open nodes to visited nodes (how much of soln space explored)
    # df["fracBoolVars"] = df['boolVars'] / (df['vars'] + sys.float_info.epsilon)  # num bools / total num of vars
    # df["fracPropVars"] = df['propagations'] / (
    #         df['vars'] + sys.float_info.epsilon)  # num propagations/ total num of vars
    # df["frac_unassigned"] = df['unassnVar'] / (2**df['vars'])  # current assignments/ total vars
    # df["fracLongClauses"] = df['long'] + df['bin'] + df[
    #     'tern']  # fraction of learnt clauses that have more than 3 literals
    # df["freqBackjumps"] = df['back_jumps'] / (df['search_time'] + sys.float_info.epsilon)
    # del df["unassnVar"]
    
    #Equations to match report:
    df["unassn_var"] = (2**df['vars']) - (df['decisions'] + df['propagations']) # decisions --> nodes (minizinc # search nodes)
    df["frac_unassn_var"] = df['unassn_var']  / (df['vars'] + sys.float_info.epsilon)  #number of unassn vars/ total nmber of vars
    df["frac_prop_vars"] = df['propagations'] / (df['vars'] + sys.float_info.epsilon)  # num propagations/ total num of vars
    df['frac_unobs_obs'] = ((2**df['vars']) - df['decisions']) / df['decisions'] # unobserved nodes/ observed nodes. prev. df["fracOpenVisit"]; decisions --> minizinc # search nodes
    df["frac_conflicts_unassn"] = df['conflicts'] / df['unassnVar']         # num failures/ num open nodes. Prev: df["fracFailUnassn"]
    df["freq_backjumps"] = df['back_jumps'] / (df['search_time'] + sys.float_info.epsilon)
    df["frac_bool_vars"] = df['boolVars'] / (df['vars'] + sys.float_info.epsilon)  # num bools / total num of vars
    df["fracLongClauses"] = df['long']/(df['long'] + df['bin'] + df['tern'])
    
    #additional var not in report: (why do we only take engine propagations?)
    df["frac_all_prop_vars"] = (df['propagations']+ df['sat_propagations'])/ (df['vars'] + sys.float_info.epsilon)  # num propagations/ total num of vars
    df["unassn_var_all_prop"] = (2**df['vars']) - (df['decisions'] + df['propagations']+ df['sat_propagations']) # decisions --> nodes (minizinc # search nodes)
    df["frac_unassn_var_all_prop"] = df['unassn_var']  / (df['vars'] + sys.float_info.epsilon)  #number of unassn vars/ total nmber of vars
    
    return df


def gradients(df_prev, df_curr):
    #For previous equations:
    # keys = ['conflicts', 'ewma_conflicts', 'decisions', 'search_iterations', 'opennodes', 'ewma_opennodes',
    #         'vars', 'back_jumps', 'ewma_back_jumps', 'solutions', 'total_time', 'intVars', 'search_time',
    #         'propagations', 'sat_propagations', 'ewma_propagations', 'propagators', 'boolVars', 'learnt',
    #         'bin', 'tern', 'long', 'peak_depth', 'decision_level_engine', 'ewma_decision_level_engine',
    #         'decision_level_treesize', 'clause_mem', 'prop_mem',
    #         'fracOpenVisit', 'fracBoolVars', 'fracPropVars', 'freqBackjumps']
    
    # Addaing vars from "Equations to match report"
    keys = ['conflicts', 'ewma_conflicts', 'decisions', 'search_iterations', 'opennodes', 'ewma_opennodes',
            'vars', 'back_jumps', 'ewma_back_jumps', 'solutions', 'total_time', 'intVars', 'search_time',
            'propagations', 'sat_propagations', 'ewma_propagations', 'propagators', 'boolVars', 'learnt',
            'bin', 'tern', 'long', 'peak_depth', 'decision_level_engine', 'ewma_decision_level_engine',
            'decision_level_treesize', 'clause_mem', 'prop_mem',
            'unassn_var', 'frac_unassn_var', 'frac_prop_vars', 'frac_unobs_obs', 'frac_conflicts_unassn',
            'freq_backjumps', 'frac_bool_vars', 'fracLongClauses']
    for i in keys:
        df_curr[i + '_gradient'] = (df_curr[i] - df_prev[i]) / 0.05 * 7200 #0.05 or 0.005
    return df_curr


def create_features_at_percent(df, lag: int) -> dict[int, list]:
    features_at_percent = {}

    for i in track(range(1, 200), description="Creating features at percent (every half percent)", transient=True):
        df_percent = []
        for id, problem in df.iterrows():

            if i in problem.statistics:
                p = problem.statistics[i]

                # Apparently there are four instances that do not have all keys. No clue what happened there.
                if len(p.keys()) != 33:
                    continue

                new_p = dict(p)
                new_p = cleanup(new_p)

                new_p['mzn'] = problem['mzn']
                new_p['dzn'] = problem['dzn']
                new_p['solved_within_time_limit'] = problem['normal_time'] < 7199

                if i >= lag:
                    if (i - lag) in features_at_percent and id in features_at_percent[i - lag].index:
                        new_p = gradients(features_at_percent[i - lag].loc[id], new_p)
                        new_p['has_gradients'] = True
                    else:
                        new_p['has_gradients'] = False
                df_percent.append((id, new_p))

        df_i = pd.DataFrame([a[1] for a in df_percent], index=[a[0] for a in df_percent])
        features_at_percent[i] = df_i

    return features_at_percent


def split_into_train_and_test(features_at_percent):
    train_at_percentage = {}
    test_at_percentage = {}

    for percentage in range(1, 40):
        labels = features_at_percent[percentage]['solved_within_time_limit']
        train, test = train_test_split(features_at_percent[percentage], test_size=0.1, random_state=0, stratify=labels)
        train_at_percentage[percentage] = train
        test_at_percentage[percentage] = test

    return train_at_percentage, test_at_percentage


def main():
    """
    Script to convert the problem output json files to a pickle of a
    dictionary of features at each percentage of the time limit.
    """
    parser = ArgumentParser(description="Convert output json files to features at percent")
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Directory containing the output json files",
    )
    parser.add_argument(
        "--output_filename",
        type=str,
        required=True,
        help="File to save the features at percent pickle file to",
    )
    parser.add_argument(
        "--num_processes",
        type=int,
        default=1,
        help="Number of processes to use for multiprocessing",
    )
    parser.add_argument(
        "--lag",
        type=int,
        default=1,
        help="Amount of timesteps for the lag of the gradient",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_filename = args.output_filename
    output_dir = Path(args.output_filename).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Created output directory {output_dir}")

    # Load the problem output json files into a dataframe
    df = load_to_dataframe(input_dir)
    logger.info(f"Loaded {len(df)} problem output json files into a dataframe")

    # Create features at each percentage of the time limit
    features_at_percent = create_features_at_percent(df, args.lag)
    logger.info("Created features at each percentage of the time limit")

    train, test = split_into_train_and_test(features_at_percent)

    with open(f"{output_filename}_train.pkl", "wb") as f:
        pickle.dump(train, f)

    with open(f"{output_filename}_test.pkl", "wb") as f:
        pickle.dump(test, f)
    logger.info(f"Saved features at percent dict to {output_filename}")


if __name__ == "__main__":
    main()

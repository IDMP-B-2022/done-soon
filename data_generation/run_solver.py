import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from subprocess import DEVNULL, PIPE, Popen, run
from sys import path
from typing import Dict, List

import pymongo
from dacite import from_dict
from bson.objectid import ObjectId

CONN_STR = "mongodb://admin:test@localhost/"
PORT = 27017
DB_NAME = 'done_soon'

SAVE_POINT_INCREMENTS = 0.5  # 0.5 means every half of a percent


@dataclass
class StatisticsSnapshot:
    percent: int  # percentage of time-limit (TL) at which the capture occurs
    features: Dict[str, float] = field(default_factory=dict)


@dataclass
class Problem:
    _id: ObjectId
    mzn: str
    dzn: str or None
    solved: bool = False  # solved within TL
    time_to_solution: float or None = None
    type: str = 'SAT'
    statistics: List[StatisticsSnapshot] = field(default_factory=list)


def run_problem(problem, executable: path = 'minizinc',
                time_limit: int = 7200000, save_percentages: List[int] = [5, 10, 15, 20],
                solver: str = 'org.chuffed.modded-chuffed') -> Problem:
    """
    Runs a given `problem` in MiniZinc. By default it uses our modified chuffed
    solver (must first be compiled and then configured in MiniZinc). It has a time
    limit (TL) and saves all the output features at certain `save_points` percentages
    of that TL.

    Args:
        problem:
            Object with all details regarding a problem instance.
        executable:
            Name of the executable (MiniZinc in our case)
        time_limit:
            The number of milleseconds at which to terminate the MiniZinc solving process.
            Also referred to as the "TL" in our work.
        save_percentages:
            List of percentages of the `time_limit` at which to save the features
            (ex: [5, 10, 15] saves at 5%, 10%, and 15%)
        solver:
            ID of the solver (modified version of Chuffed in our case). Corresponds to the
            solver ID in MiniZinc (in our case in Ubuntu this is in
            ~/.minizinc/solvers/modded-chuffed.msc)

    """

    # error checking
    if run(['which', executable], stdout=DEVNULL).returncode != 0:
        raise FileNotFoundError(f'Executable ({executable}) was not found')
    if solver not in str(run([executable, '--solvers'], stdout=PIPE).stdout):
        raise FileNotFoundError(f'Solver ({solver}) was not found')
    if not os.path.exists(problem.mzn):
        raise FileNotFoundError(f'Model ({problem.model}) was not found')
    if problem.dzn and not os.path.exists(problem.dzn):
        raise FileNotFoundError(f'Problem instance ({problem.dzn}) was not found')

    save_idx = 0

    exec_args = ['--solver', solver, '-t', str(time_limit), '--json-stream', '--output-time']

    if problem.dzn is not None:
        command = [executable, problem.mzn, problem.dzn] + exec_args
    else:
        command = [executable, problem.mzn] + exec_args

    proc = Popen(command, stdout=PIPE)

    # process output line-by-line
    for line in proc.stdout:
        try:
            jsonified_line = json.loads(line)
        except json.JSONDecodeError as e:
            print(e.msg, file = sys.stderr)
            continue
        else:
            match jsonified_line['type']:
                case 'status':
                    if jsonified_line['status'] == 'OPTIMAL_SOLUTION':
                        problem.type = 'OPT'
                case 'solution':
                    problem.solved = True
                    problem.time_to_solution = jsonified_line['time']
                case 'statistics':
                    elapsed_time = jsonified_line['statistics']['optTime']
                    if reached_save_point(elapsed_time, time_limit, save_percentages, save_idx):
                        # made it to a save point
                        save_idx += 1
                        snapshot = StatisticsSnapshot(elapsed_time/time_limit, jsonified_line)
                        problem.statistics += snapshot

    proc.wait()

    return problem


def reached_save_point(elapsed: float, timeout: int, save_percentages: List[int], save_idx: int) -> bool:
    """
    Whenever MiniZinc reaches a percentage of the TL that we want to save
    """
    if save_idx == len(save_percentages):  # no more points to save (reached end of the list)
        return False
    percentage_time_elapsed = elapsed / (timeout / 1000)  # timeout in ms
    save_point_percentage = save_percentages[save_idx] / 100

    return percentage_time_elapsed >= save_point_percentage

def read_next_problem_from_db(db, features_or_label):
    """
    Reads the next problem from a todo collection from the mongo `db`.
    The method `find_one_and_update(...)` blocks other processes from
    reading the same problem before the current process 'claims' it.
    """
    todo = db.todo  # empty todo collection if didn't exist
    found = todo.find_one_and_update(
        {f'claimed_{features_or_label}_generation': False},
        {'$set': {f'claimed_{features_or_label}_generation': True}}
    )

    return found
    

def mark_id_as_completed(db, problem, features_or_label):
    todo = db.todo
    todo.find_one_and_update(
        {'_id': problem._id},
        {'$set': {f'generated_{features_or_label}': True}}
    )

def update_result_in_db(db, problem):
    collected = db.collected_data
    collected.update_one(
        {'_id': problem._id},
        {'$set':
            {
                'statistics': problem.statistics,
                'time_to_solution': problem.time_to_solution,
                'solved': problem.solved,
                'type': problem.type
            }
        },
        upsert = True
    )

def main():
    parser = argparse.ArgumentParser(description='Run parser for either label or feature collection.')
    parser.add_argument('--mode', choices=['label', 'features'], required=True)
    args = parser.parse_args()
    # set a 5-second connection timeout
    mongo_client = pymongo.MongoClient(CONN_STR, PORT, serverSelectionTimeoutMS=5000)
    db = mongo_client[DB_NAME]

    next_problem = read_next_problem_from_db(db, args.mode)

    save_points = [x / (1 / SAVE_POINT_INCREMENTS)
        for x in range(100 * int(1 / SAVE_POINT_INCREMENTS))
    ]

    while next_problem is not None:
        problem = from_dict(Problem, next_problem)
        print(f"Running id: {problem._id}, model: {problem.mzn}, instance: {problem.dzn}")
        if args.mode == "label":
            problem = run_problem(problem, save_percentages=save_points, solver='org.chuffed.chuffed')
        else:
            problem = run_problem(problem, save_percentages=save_points)

        update_result_in_db(db, problem)

        mark_id_as_completed(db, problem, args.mode)
        next_problem = read_next_problem_from_db(db, args.mode)


if __name__ == '__main__':
    main()

import json
import os
import pymongo
import time
from dataclasses import dataclass, field
from subprocess import DEVNULL, PIPE, Popen, run
from sys import path
from typing import Dict, List


CONN_STR = "mongodb://admin:test@localhost/"
PORT = 27017
DB_NAME = 'done_soon'

SAVE_POINT_INCREMENTS = 0.5  # 0.5 means every half of a percent


@dataclass
class Output:
    percent: int = -1  # percentage of time-limit (TL) at which the capture occurs
    features: Dict[str, float] = field(default_factory=dict)


@dataclass
class ProblemResults:
    model: str
    problem_instance: str
    solved: bool = False  # solved within TL
    results: List[Output] = field(default_factory=list)


def run_problem(model: path, problem_instance: path or None, executable: path = 'minizinc',
                time_limit: int = 7200000, save_percentages: List[int] = [5, 10, 15, 20],
                solver: str = 'org.chuffed.modded-chuffed') -> ProblemResults:
    """
    Runs a given `problem` in MiniZinc. By default it uses our modified chuffed
    solver (must first be compiled and then configured in MiniZinc). It has a time
    limit (TL) and saves all the output features at certain `save_points` percentages
    of that TL.

    Args:
        model:
            Path to the model (.mzn) file.
        problem_instance:
            Path to the problem instance in case it exists
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
    if not os.path.exists(model):
        raise FileNotFoundError(f'Model ({model}) was not found')
    if problem_instance and not os.path.exists(problem_instance):
        raise FileNotFoundError(f'Problem instance ({problem_instance}) was not found')

    # setup
    results = []
    problem_info = {
        'type': ''
    }
    save_idx = 0

    found_solution = False

    if problem_instance is not None:
        command = [executable, model, problem_instance, '--solver', solver, '-t', str(time_limit)]
    else:
        command = [executable, model, '--solver', solver, '-t', str(time_limit), '']

    proc = Popen(command, stdout=PIPE)

    # process output line-by-line
    for line in proc.stdout:
        try:
            jsonified_line = json.loads(line)
        except:
            pass  # we don't care about non-json lines

        if is_solution_line(jsonified_line):
            found_solution = True

        if is_statistics_line(jsonified_line):
            # check if we need to capture
            elapsed_time = jsonified_line['statistics']['optTime']
            if reached_save_point(elapsed_time, time_limit, save_percentages, save_idx):
                # made it to a save point
                save_idx += 1
                results += jsonified_line['statistics']

    proc.wait()

    return results

def is_statistics_line(line: dict) -> bool:
    return line['type'] == 'statistics'


def is_solution_line(line: dict) -> bool:
    return line['type'] == 'solution'


def reached_save_point(elapsed: float, timeout: int, save_percentages: List[int], save_idx: int) -> bool:
    """
    Whenever MiniZinc reaches a checkpoint
    """
    if save_idx == len(save_percentages):  # no more points to save (reached end of the list)
        return False
    percentage_time_elapsed = elapsed / (timeout / 1000)  # timeout in ms
    save_point_percentage = save_percentages[save_idx] / 100

    return percentage_time_elapsed >= save_point_percentage

def read_next_problem_from_db(db):
    """
    Reads the next problem from a todo collection from the mongo `db`.
    The method `find_one_and_update(...)` blocks other processes from
    reading the same problem before the current process 'claims' it.
    """
    todo = db.todo  # empty todo collection if didn't exist
    found = todo.find_one_and_update(
        {'claimed_feature_generation': False},
        {'$set': {'claimed_feature_generation': True}}
    )

    return found


def insert_result_set_in_db(db_path, mzn, dzn, problem_results):
    """
    
    """
    

def mark_id_as_completed(db, id):
    todo = db.todo
    todo.find_one_and_update(
        {'_id': id},
        {'$set': {'generated_features'}}
    )


if __name__ == '__main__':
    # set a 5-second connection timeout
    mongo_client = pymongo.MongoClient(CONN_STR, PORT, serverSelectionTimeoutMS=5000)
    db = mongo_client[DB_NAME]

    next_problem = read_next_problem_from_db(db)

    save_points = [x / (1 / SAVE_POINT_INCREMENTS)
        for x in range(100 * int(1 / SAVE_POINT_INCREMENTS))
    ]

    while next_problem is not None:
        id, mzn, dzn = next_problem['_id'], next_problem['mzn'], next_problem['dzn']
        print(f"Running id: {id}, model: {mzn}, instance: {dzn}")
        problem_results = run_problem(mzn, dzn, save_percentages=save_points)

        insert_result_set_in_db(db, mzn, dzn, problem_results)

        mark_id_as_completed(mongo_client, id)
        next_problem = read_next_problem_from_db(db)

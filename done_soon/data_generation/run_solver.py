"""
Coordinates the loading of problems from the database, the running of said problems
and the eventual storage of their statistics in the database.
"""
import argparse
import json
import os
import sys
from subprocess import DEVNULL, PIPE, CalledProcessError, Popen, run
from sys import path

import pymongo
from dacite import from_dict

from db_datastructs import Problem, StatisticsSnapshot
from db_functions import (mark_id_as_completed, read_next_problem_from_db,
                          update_result_in_db)


def run_problem(problem: Problem, executable: path = 'minizinc',
                time_limit: int = 7200000, save_percentages: list[int] = None,
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
    if save_percentages is None:
        save_percentages = [5, 10, 15, 20]
    save_idx = 0

    exec_args = ['--solver', solver, '-t',
                 str(time_limit), '--json-stream', '--output-time']

    if problem.dzn is not None:
        command = [executable, problem.mzn, problem.dzn] + exec_args
    else:
        command = [executable, problem.mzn] + exec_args

    proc = Popen(command, stdout=PIPE)

    # process output line-by-line
    for line in proc.stdout:
        try:
            jsonified_line = json.loads(line)
        except json.JSONDecodeError as exc:
            print(exc.msg, file=sys.stderr)
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
                        snapshot = StatisticsSnapshot(
                            elapsed_time/time_limit, jsonified_line)
                        problem.statistics += snapshot

    proc.wait()

    return problem


def reached_save_point(
        elapsed: float, timeout: int, save_percentages: list[int], save_idx: int) -> bool:
    """
    Whenever MiniZinc reaches a percentage of the TL that we want to save
    """
    if save_idx == len(save_percentages):  # no more points to save (reached end of the list)
        return False
    percentage_time_elapsed = elapsed / (timeout / 1000)  # timeout in ms
    save_point_percentage = save_percentages[save_idx] / 100

    return percentage_time_elapsed >= save_point_percentage


def pre_run_error_checks(executable: str, solver: str):
    """Check whether the minizinc executable and solver exist"""
    try:
        run(['which', executable], stdout=DEVNULL, check=True)
    except CalledProcessError as exc:
        raise FileNotFoundError(
            f'Executable ({executable}) was not found') from exc
    if solver not in str(run([executable, '--solvers'], stdout=PIPE, check=True).stdout):
        raise FileNotFoundError(f'Solver ({solver}) was not found')


def per_problem_error_checks(problem: Problem):
    """Check if the mzn and dzn files exist, print pretty errors"""
    if not os.path.exists(problem.mzn):
        raise FileNotFoundError(f'Model ({problem.mzn}) was not found')
    if problem.dzn and not os.path.exists(problem.dzn):
        raise FileNotFoundError(
            f'Problem instance ({problem.dzn}) was not found')


class CommandLineArgs:
    """Defines namespace for this script's CL args"""
    mode: str
    timelimit: int
    db_addr: str
    db_username: str
    db_password: str
    db_name: str
    db_port: int
    increments: float


def parse_args():
    parser = argparse.ArgumentParser(
        description='Run parser for either label or feature collection.')
    parser.add_argument('--mode', choices=['label', 'features'], required=True)
    parser.add_argument('-t', '--timelimit', type=int, default=7200000)
    parser.add_argument('-a', '--db-addr', type=str, default='localhost')
    parser.add_argument('-u', '--db-username', type=str, default='admin')
    parser.add_argument('-p', '--db-password', type=str, default='test')
    parser.add_argument('-n', '--db-name', type=str, default='done_soon')
    parser.add_argument('-i', '--increments', type=float, default=0.5,
                        help="""
        Percentage increments at which to capture statistics. Only relevant
        when mode=features.
        """)

    args = parser.parse_args(namespace=CommandLineArgs())
    return args


def connect_and_get_database(
        username: str, password: str, addr: str, port: int, name: str):
    # set a 5-second connection timeout
    conn_str = f"mongodb://{username}:{password}@{addr}/"
    mongo_client = pymongo.MongoClient(
        conn_str, port, serverSelectionTimeoutMS=5000)
    database = mongo_client[name]
    return database


def generate_save_points(save_point_increments):
    points = [x / (1 / save_point_increments)
              for x in range(100 * int(1 / save_point_increments))
              ]
    return points


def main():
    """
    Parses command line arguments, loads problems from DB, runs them, and stores results.
    """
    args = parse_args()
    database = connect_and_get_database(
        args.db_username, args.db_password, args.db_addr, args.db_port, args.db_name)

    executable = 'minizinc'
    solver = 'org.chuffed.modded-chuffed'

    if args.mode == "label":
        solver = 'org.chuffed.chuffed'  # use the normal `chuffed` to generate labels
    pre_run_error_checks(executable, solver)

    save_points = generate_save_points(args.increments)
    next_problem = read_next_problem_from_db(database, args.mode)

    while next_problem is not None:
        problem = from_dict(Problem, next_problem)
        problem.time_limit = args.timelimit

        per_problem_error_checks(problem)

        print(
            f"Running id: {problem._id}, model: {problem.mzn}, instance: {problem.dzn}")

        problem = run_problem(
            problem,
            save_percentages=save_points,
            solver=solver,
            executable=executable)

        update_result_in_db(database, problem)

        mark_id_as_completed(database, problem, args.mode)
        next_problem = read_next_problem_from_db(database, args.mode)


if __name__ == '__main__':
    main()

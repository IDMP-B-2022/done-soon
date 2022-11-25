import argparse
import logging
import os
from pathlib import Path
from subprocess import DEVNULL, PIPE, CalledProcessError, run

import pymongo
from dacite import from_dict
from pymongo.database import Database
from done_soon.data_generation import db
from done_soon.data_generation import solve_problem

worker_logger = logging.getLogger("generate_data.worker")
worker_logger.setLevel(logging.DEBUG)


def pre_run_error_checks(executable: str, solver: str, data_dir: Path):
    """Check whether the minizinc executable and solver exist"""
    try:
        run(['which', executable], stdout=DEVNULL, check=True)
    except CalledProcessError as exc:
        raise FileNotFoundError(
            f'Executable ({executable}) was not found') from exc
    if solver not in str(run([executable, '--solvers'], stdout=PIPE, check=True).stdout):
        raise FileNotFoundError(f'Solver ({solver}) was not found')
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f'Data dir ({data_dir}) not found')


def per_problem_error_checks(problem: db.datastructs.Problem, data_dir: Path):
    """Check if the mzn and dzn files exist, print pretty errors"""
    if not os.path.exists(data_dir / problem.mzn):
        raise FileNotFoundError(
            f'Model ({data_dir / problem.mzn}) was not found')
    if problem.dzn and not os.path.exists(data_dir / problem.dzn):
        raise FileNotFoundError(
            f'Problem instance ({data_dir / problem.dzn}) was not found')


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


class WorkerArgs(argparse.Namespace):
    mode: str
    timelimit: int
    db_addr: str
    db_username: str
    db_password: str
    db_name: str
    db_port: int
    increments: float
    data: Path


def process_problems(args: WorkerArgs, database: Database):
    executable = 'minizinc'
    solver = 'org.chuffed.modded-chuffed'

    if args.mode == "label":
        solver = 'org.chuffed.chuffed'  # use the normal `chuffed` to generate labels
    pre_run_error_checks(executable, solver, args.data)

    save_points = generate_save_points(args.increments)
    next_problem = db.functions.read_next_problem(database, args.mode)

    while next_problem is not None:
        problem = from_dict(db.datastructs.Problem, next_problem)
        problem.time_limit = args.timelimit

        per_problem_error_checks(problem, args.data)

        worker_logger.info("Running id: %s, model: %s, instance: %s",
                           problem.id, problem.mzn, problem.dzn)

        try:
            problem = solve_problem(
                problem,
                args.data,
                args.mode,
                save_percentages=save_points,
                solver=solver,
                executable=executable)
        except RuntimeError:
            db.functions.mark_id_as_completed(database, problem, args.mode, error=True)
            db.functions.update_result(database, problem)
        else:
            db.functions.mark_id_as_completed(database, problem, args.mode)
            db.functions.update_result(database, problem)
            worker_logger.info("Finished id: %s, model: %s, instance: %s",
                 problem.id, problem.mzn, problem.dzn)

        next_problem = db.functions.read_next_problem(database, args.mode)


def add_args(parser: argparse.ArgumentParser):
    parser.add_argument('--mode', choices=['label', 'features'], required=True)
    parser.add_argument('-t', '--timelimit', type=int, default=7200000)
    parser.add_argument('-a', '--db-addr', type=str, default='localhost')
    parser.add_argument('--db-port', type=int, default=27017)
    parser.add_argument('-u', '--db-username', type=str, default='admin')
    parser.add_argument('-p', '--db-password', type=str, default='test')
    parser.add_argument('-n', '--db-name', type=str, default='done_soon')
    parser.add_argument('-i', '--increments', type=float, default=0.5,
                        help="""
        Percentage increments at which to capture statistics. Only relevant
        when mode=features.
        """)
    parser.add_argument('-d', '--data', type=Path,
                        help="Path to Problems folder", required=True)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Run solver for either label or feature collection.')
    add_args(parser)
    args = parser.parse_args(namespace=WorkerArgs())
    return args


def start_worker(args: WorkerArgs):
    database = connect_and_get_database(
        args.db_username, args.db_password, args.db_addr, args.db_port, args.db_name)

    process_problems(args, database)


def main():
    """
    Parses command line arguments.
    """
    args = parse_args()
    start_worker(args)


if __name__ == '__main__':
    main()

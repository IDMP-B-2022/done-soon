import os
from sys import path
import time
import logging

from dataclasses import dataclass, field
from subprocess import Popen, DEVNULL, PIPE, run
from typing import List, Dict

import sqlite3


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


def run_problem(model: path, problem_instance: path, executable: path = 'minizinc',
                timeout: int = 7200, save_points: List[int] = [5, 10, 15, 20],
                solver: str = 'org.chuffed.modded-chuffed') -> ProblemResults:
    """
    Runs a given `problem` in MiniZinc. By default it uses our modified chuffed
    solver (must first be compiled and then configured in MiniZinc). It has a time
    limit (TL) and saves all the output features at certain `save_points` percentages
    of that TL.
    """
    # error checking
    if run(['which', executable], stdout=DEVNULL).returncode != 0:
        raise FileNotFoundError(f'Executable ({executable}) was not found')
    if not os.path.exists(model):
        raise FileNotFoundError(f'Model ({model}) was not found')
    if not os.path.exists(problem_instance):
        raise FileNotFoundError(f'Problem instance ({problem_instance}) was not found')


    # setup
    problem_results = ProblemResults(model, problem_instance)
    command = [executable, model, problem_instance, '--solver', solver]
    proc = Popen(command, stdout=PIPE)
    start_time = time.time()

    save_points.append(float('inf'))
    next_save = save_points.pop(0)
    output = Output(percent=next_save)

    capture_next_block = False
    is_next_block = False

    # process output
    for line in proc.stdout:
        line = line.decode('utf-8')
        elapsed = time.time() - start_time

        if is_stat_related(line):
            # check if we need to capture
            if not capture_next_block and elapsed / timeout > next_save / 100:
                # made it to a save point
                capture_next_block = True
                next_save = save_points.pop(0)
            if capture_next_block and is_next_block:
                if is_stat_value(line):  # new value to save
                    name, stat = line[13:].split('=')
                    output.features[name] = float(stat)
                    print(name, output.features[name])

                elif stat_block_end(line):  # end of stat block to capture
                    capture_next_block = False
                    is_next_block = False
                    problem_results.results.append(output)
                    output = Output(percent=next_save)

            elif capture_next_block and stat_block_end(line):  # new stat block starts next line
                    is_next_block = True


    # check result
    res = proc.wait()
    if res != 0:
        problem_results.solved = False
    else:
        problem_results.solved = True
    return problem_results


def is_stat_related(line: str) -> bool:
    """
    Log lines from MiniZinc that are in any way related to statistics
    start from "%%%mzn-stat"
    """
    return line[:11] == '%%%mzn-stat'


def is_stat_value(line: str) -> bool:
    """
    Log lines from MiniZinc that have statistics values start
    with "%%%mzn-stat: "
    """
    return line[:13] == '%%%mzn-stat: '


def stat_block_end(line: str) -> bool:
    """
    The line "%%%mzn-stat-end" is output at the end of each block of
    statistics from MiniZinc.
    """
    return line[:15] == '%%%mzn-stat-end'

def read_next_problem_from_db(db_path):
    """
    Reads the next problem from a todo table from a sqlite3 db at `db_path`.
    Problem consists of an id and a model with a optional problem instance.
    Returns (None, None, None) if no more problems are in the table.
    """
    db = sqlite3.connect(db_path)
    cursor = db.cursor()
    cursor.execute("SELECT id, mzn, dzn from todo limit 1;")
    values = cursor.fetchone()
    db.close()
    if len(values) == 0:
        return (None, None, None)
    return values[0]

def insert_result_set_in_db(db_path, result_set):
    """
    Inserts a `result_set` into a sqlite3 db at `db_path`.
    """
def setup_db(db_path):
    """
    Inserts a feature table into a sqlite3 db at `db_path`
    """
    db = sqlite3.connect(db_path)
    cursor = db.cursor()
    feature_table = """
    CREATE TABLE IF NOT EXISTS features (
            mzn VARCHAR(255) not null,
            dzn VARCHAR(255) not null,
            PRIMARY KEY(mzn, dzn)
    ); """
    db.commit()
    db.close()

def remove_id_from_todo_list(db_path, id):
    db = sqlite3.connect(db_path)
    cursor = db.cursor()
    cursor.execute("DELETE FROM todo WHERE id=(?)", (id,))
    db.commit()
    db.close()

if __name__ == '__main__':
    db_path = 'output.db'
    setup_db(db_path)

    id, mzn, dzn = read_next_problem_from_db(db_path)
    while mzn != None:
        result_set = run_problem(mzn, dzn, save_points=[0, 0.05, 0.1, 0.15, 0.2])
        insert_result_set_in_db(db_path, mzn, dzn, result_set)
        remove_id_from_todo_list(db_path, id)

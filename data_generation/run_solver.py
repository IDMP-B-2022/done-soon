import os
import sqlite3
import time
from dataclasses import dataclass, field
from subprocess import DEVNULL, PIPE, Popen, run
from sys import path
from typing import Dict, List


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
                timeout: int = 7200000, save_points: List[int] = [5, 10, 15, 20],
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
    if problem_instance and not os.path.exists(problem_instance):
        raise FileNotFoundError(f'Problem instance ({problem_instance}) was not found')


    # setup
    problem_results = ProblemResults(model, problem_instance)
    
    if problem_instance != None:
        command = [executable, model, problem_instance, '--solver', solver, '-t', str(timeout)]
    else:
        command = [executable, model, '--solver', solver, '-t', str(timeout)]

    proc = Popen(command, stdout=PIPE)
    start_time = time.time()

    save_points.append(float('inf'))
    next_save = save_points.pop(0)
    output = Output(percent=next_save)

    capture_next_block = False
    is_next_block = False

    found_one_solution = False

    # process output
    for line in proc.stdout:
        line = line.decode('utf-8')
        if not found_one_solution and line == '----------':
            found_one_solution = True
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

                elif stat_block_end(line):  # end of stat block to capture
                    capture_next_block = False
                    is_next_block = False
                    problem_results.results.append(output)
                    output = Output(percent=next_save)

            elif capture_next_block and stat_block_end(line):  # new stat block starts next line
                    is_next_block = True


    # wait for result
    proc.wait()
    problem_results.solved = found_one_solution

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
    values = cursor.fetchall()
    db.close()
    if len(values) == 0:
        return (None, None, None)
    return values[0]

def insert_result_set_in_db(db_path, mzn, dzn, result_set):
    """
    Inserts a `result_set` into a sqlite3 db at `db_path`.
    """
    db = sqlite3.connect(db_path)
    cursor = db.cursor()

    result_set.results()
    cursor.execute("""
        INSERT INTO features(
            mzn,
            dzn,

            p5_conflicts,
            p5_ewma_conflicts,
            p5_nodes,
            p5_ewma_opennodes,
            p5_vars,
            p5_back_jumps,
            p5_ewma_back_jumps,
            p5_solutions,
            p5_total_time,
            p5_search_time,
            p5_intVars,
            p5_propagations,
            p5_ewma_propagations,
            p5_propagators,
            p5_boolVars,
            p5_learnt,
            p5_bin,
            p5_tern,
            p5_long_vars,
            p5_peak_depth,
            p5_best_objective,
            p5_ewma_best_objective,

            p10_conflicts,
            p10_ewma_conflicts,
            p10_nodes,
            p10_ewma_opennodes,
            p10_vars,
            p10_back_jumps,
            p10_ewma_back_jumps,
            p10_solutions,
            p10_total_time,
            p10_search_time,
            p10_intVars,
            p10_propagations,
            p10_ewma_propagations,
            p10_propagators,
            p10_boolVars,
            p10_learnt,
            p10_bin,
            p10_tern,
            p10_long_vars,
            p10_peak_depth,
            p10_best_objective,
            p10_ewma_best_objective,

            p15_conflicts,
            p15_ewma_conflicts,
            p15_nodes,
            p15_ewma_opennodes,
            p15_vars,
            p15_back_jumps,
            p15_ewma_back_jumps,
            p15_solutions,
            p15_total_time,
            p15_search_time,
            p15_intVars,
            p15_propagations,
            p15_ewma_propagations,
            p15_propagators,
            p15_boolVars,
            p15_learnt,
            p15_bin,
            p15_tern,
            p15_long_vars,
            p15_peak_depth,
            p15_best_objective,
            p15_ewma_best_objective,

            p20_conflicts,
            p20_ewma_conflicts,
            p20_nodes,
            p20_ewma_opennodes,
            p20_vars,
            p20_back_jumps,
            p20_ewma_back_jumps,
            p20_solutions,
            p20_total_time,
            p20_search_time,
            p20_intVars,
            p20_propagations,
            p20_ewma_propagations,
            p20_propagators,
            p20_boolVars,
            p20_learnt,
            p20_bin,
            p20_tern,
            p20_long_vars,
            p20_peak_depth,
            p20_best_objective,
            p20_ewma_best_objective,
        ) VALUES(
            ?, ?, ?, ?, ?,, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        ) """
        , (
            mzn,
            dzn,

            result_set[0].features['conflicts'],
            result_set[0].features['ewma_conflicts'],
            result_set[0].features['nodes'],
            result_set[0].features['ewma_opennodes'],
            result_set[0].features['vars'],
            result_set[0].features['back_jumps'],
            result_set[0].features['conflicts'],
            result_set[0].features['ewma_back_jumps'],
            result_set[0].features['solutions'],
            result_set[0].features['total_time'],
            result_set[0].features['search_time'],
            result_set[0].features['intVars'],
            result_set[0].features['propagations'],
            result_set[0].features['ewma_propagations'],
            result_set[0].features['propagators'],
            result_set[0].features['boolVars'],
            result_set[0].features['learnt'],
            result_set[0].features['bin'],
            result_set[0].features['tern'],
            result_set[0].features['long'],
            result_set[0].features['peak_depth'],
            result_set[0].features['best_objective'],
            result_set[0].features['ewma_best_objective'],

            result_set[1].features['conflicts'],
            result_set[1].features['ewma_conflicts'],
            result_set[1].features['nodes'],
            result_set[1].features['ewma_opennodes'],
            result_set[1].features['vars'],
            result_set[1].features['back_jumps'],
            result_set[1].features['conflicts'],
            result_set[1].features['ewma_back_jumps'],
            result_set[1].features['solutions'],
            result_set[1].features['total_time'],
            result_set[1].features['search_time'],
            result_set[1].features['intVars'],
            result_set[1].features['propagations'],
            result_set[1].features['ewma_propagations'],
            result_set[1].features['propagators'],
            result_set[1].features['boolVars'],
            result_set[1].features['learnt'],
            result_set[1].features['bin'],
            result_set[1].features['tern'],
            result_set[1].features['long'],
            result_set[1].features['peak_depth'],
            result_set[1].features['best_objective'],
            result_set[1].features['ewma_best_objective'],

            result_set[2].features['conflicts'],
            result_set[2].features['ewma_conflicts'],
            result_set[2].features['nodes'],
            result_set[2].features['ewma_opennodes'],
            result_set[2].features['vars'],
            result_set[2].features['back_jumps'],
            result_set[2].features['conflicts'],
            result_set[2].features['ewma_back_jumps'],
            result_set[2].features['solutions'],
            result_set[2].features['total_time'],
            result_set[2].features['search_time'],
            result_set[2].features['intVars'],
            result_set[2].features['propagations'],
            result_set[2].features['ewma_propagations'],
            result_set[2].features['propagators'],
            result_set[2].features['boolVars'],
            result_set[2].features['learnt'],
            result_set[2].features['bin'],
            result_set[2].features['tern'],
            result_set[2].features['long'],
            result_set[2].features['peak_depth'],
            result_set[2].features['best_objective'],
            result_set[2].features['ewma_best_objective'],

            result_set[3].features['conflicts'],
            result_set[3].features['ewma_conflicts'],
            result_set[3].features['nodes'],
            result_set[3].features['ewma_opennodes'],
            result_set[3].features['vars'],
            result_set[3].features['back_jumps'],
            result_set[3].features['conflicts'],
            result_set[3].features['ewma_back_jumps'],
            result_set[3].features['solutions'],
            result_set[3].features['total_time'],
            result_set[3].features['search_time'],
            result_set[3].features['intVars'],
            result_set[3].features['propagations'],
            result_set[3].features['ewma_propagations'],
            result_set[3].features['propagators'],
            result_set[3].features['boolVars'],
            result_set[3].features['learnt'],
            result_set[3].features['bin'],
            result_set[3].features['tern'],
            result_set[3].features['long'],
            result_set[3].features['peak_depth'],
            result_set[3].features['best_objective'],
            result_set[3].features['ewma_best_objective'],
            result_set.solved
        )
    )

    db.commit()
    db.close()


def setup_db(db_path):
    """
    Inserts a feature table into a sqlite3 db at `db_path`
    """
    db = sqlite3.connect(db_path)
    cursor = db.cursor()
    feature_table = """ CREATE TABLE if not exists features(
            mzn VARCHAR(255) not null,
            dzn VARCHAR(255) not null,

            p5_conflicts INTEGER not null,
            p5_ewma_conflicts INTEGER not null,
            p5_nodes INTEGER not null,
            p5_ewma_opennodes INTEGER not null,
            p5_vars INTEGER not null,
            p5_back_jumps INTEGER not null,
            p5_ewma_back_jumps INTEGER not null,
            p5_solutions INTEGER not null,
            p5_total_time REAL not null,
            p5_search_time REAL not null,
            p5_intVars INTEGER not null,
            p5_propagations INTEGER not null,
            p5_ewma_propagations INTEGER not null,
            p5_propagators INTEGER not null,
            p5_boolVars INTEGER not null,
            p5_learnt INTEGER not null,
            p5_bin INTEGER not null,
            p5_tern INTEGER not null,
            p5_long_vars INTEGER not null,
            p5_peak_depth INTEGER not null,
            p5_best_objective INTEGER,
            p5_ewma_best_objective INTEGER,
            p5_time_limit_reached BOOLEAN not null,

            p10_conflicts INTEGER not null,
            p10_ewma_conflicts INTEGER not null,
            p10_nodes INTEGER not null,
            p10_ewma_opennodes INTEGER not null,
            p10_vars INTEGER not null,
            p10_back_jumps INTEGER not null,
            p10_ewma_back_jumps INTEGER not null,
            p10_solutions INTEGER not null,
            p10_total_time REAL not null,
            p10_search_time REAL not null,
            p10_intVars INTEGER not null,
            p10_propagations INTEGER not null,
            p10_ewma_propagations INTEGER not null,
            p10_propagators INTEGER not null,
            p10_boolVars INTEGER not null,
            p10_learnt INTEGER not null,
            p10_bin INTEGER not null,
            p10_tern INTEGER not null,
            p10_long_vars INTEGER not null,
            p10_peak_depth INTEGER not null,
            p10_best_objective INTEGER,
            p10_ewma_best_objective INTEGER,
            p10_time_limit_reached BOOLEAN not null,

            p15_conflicts INTEGER not null,
            p15_ewma_conflicts INTEGER not null,
            p15_nodes INTEGER not null,
            p15_ewma_opennodes INTEGER not null,
            p15_vars INTEGER not null,
            p15_back_jumps INTEGER not null,
            p15_ewma_back_jumps INTEGER not null,
            p15_solutions INTEGER not null,
            p15_total_time REAL not null,
            p15_search_time REAL not null,
            p15_intVars INTEGER not null,
            p15_propagations INTEGER not null,
            p15_ewma_propagations INTEGER not null,
            p15_propagators INTEGER not null,
            p15_boolVars INTEGER not null,
            p15_learnt INTEGER not null,
            p15_bin INTEGER not null,
            p15_tern INTEGER not null,
            p15_long_vars INTEGER not null,
            p15_peak_depth INTEGER not null,
            p15_best_objective INTEGER,
            p15_ewma_best_objective INTEGER,
            p15_time_limit_reached BOOLEAN not null,

            p20_conflicts INTEGER not null,
            p20_ewma_conflicts INTEGER not null,
            p20_nodes INTEGER not null,
            p20_ewma_opennodes INTEGER not null,
            p20_vars INTEGER not null,
            p20_back_jumps INTEGER not null,
            p20_ewma_back_jumps INTEGER not null,
            p20_solutions INTEGER not null,
            p20_total_time REAL not null,
            p20_search_time REAL not null,
            p20_intVars INTEGER not null,
            p20_propagations INTEGER not null,
            p20_ewma_propagations INTEGER not null,
            p20_propagators INTEGER not null,
            p20_boolVars INTEGER not null,
            p20_learnt INTEGER not null,
            p20_bin INTEGER not null,
            p20_tern INTEGER not null,
            p20_long_vars INTEGER not null,
            p20_peak_depth INTEGER not null,
            p20_best_objective INTEGER,
            p20_ewma_best_objective INTEGER,
            p20_time_limit_reached BOOLEAN not null,
            PRIMARY KEY(mzn, dzn)
    ); """
    cursor.execute(feature_table)
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
    remove_id_from_todo_list(db_path, id)

    save_points = [5, 10, 15, 20]

    while mzn != None:
        print(f"Running id: {id}, model: {mzn}, instance: {dzn}")
        result_set = run_problem(mzn, dzn, save_points=save_points)

        # Otherwise we don't reach 20%!
        if len(result_set.results) == len(save_points):
            insert_result_set_in_db(db_path, mzn, dzn, result_set)
        id, mzn, dzn = read_next_problem_from_db(db_path)
        remove_id_from_todo_list(db_path, id)

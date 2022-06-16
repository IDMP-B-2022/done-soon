import os
import sqlite3
import time
from dataclasses import dataclass, field
from subprocess import DEVNULL, PIPE, Popen, run
from sys import path, argv
from typing import Dict, List
import json


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
    results = ProblemResults(model, problem_instance)
    save_idx = 0
    next_save_point = save_percentages[save_idx]
    output = Output(percent=next_save_point)

    capture_next_block = False
    is_next_block = False

    found_one_solution = False

    if problem_instance is not None:
        command = [executable, model, problem_instance, '--solver', solver, '-t', str(time_limit)]
    else:
        command = [executable, model, '--solver', solver, '-t', str(time_limit)]

    proc = Popen(command, stdout=PIPE)
    start_time = time.time()

    # process output line-by-line
    for line in proc.stdout:
        line = line.decode('utf-8')
        if not found_one_solution and is_solution(line):
            found_one_solution = True
        elapsed = time.time() - start_time

        if is_stat_related(line):
            # check if we need to capture
            if not capture_next_block and reached_save_point(elapsed, time_limit, save_percentages, save_idx):
                # made it to a save point
                capture_next_block = True
                next_save_point = save_percentages[save_idx]
                save_idx += 1

            if capture_next_block and is_next_block:
                if is_stat_value(line):  # new value to save
                    name, stat = line[13:].split('=')
                    output.features[name] = float(stat)

                elif stat_block_end(line):  # end of stat block to capture
                    capture_next_block = False
                    is_next_block = False
                    results.results.append(output)
                    output = Output(percent=next_save_point)

            elif capture_next_block and stat_block_end(line):  # new stat block starts next line
                is_next_block = True

    # wait for result
    proc.wait()
    results.solved = found_one_solution

    return results


def reached_save_point(elapsed: float, timeout: int, save_percentages: List[int], save_idx: int) -> bool:
    """
    Whenever MiniZinc reaches a checkpoint
    """
    if save_idx == len(save_percentages):  # no more points to save (reached end of the list)
        return False
    percentage_time_elapsed = elapsed / (timeout / 1000)  # timeout in ms
    save_point_percentage = save_percentages[save_idx] / 100

    return percentage_time_elapsed >= save_point_percentage


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


def is_solution(line: str) -> bool:
    """
    Whenever MiniZinc finds a solution it prints '----------\n'
    """
    return line == '----------\n'


def remove_id_from_todo_list(db_path, id):
    db = sqlite3.connect(db_path)
    cursor = db.cursor()
    cursor.execute("DELETE FROM todo WHERE id=(?)", (id,))
    db.commit()
    db.close()


if __name__ == '__main__':
    result = []


    save_points = [x * 0.5 for x in range(0, 200)]

    with open('result.json', 'w') as f:
        f.write(json.dumps([
            {'percent': x.percent, 'features': x.features}
                for x in run_problem(argv[1], argv[2], save_percentages=save_points).results
        ]))

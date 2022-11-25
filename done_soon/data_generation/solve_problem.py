"""
Coordinates the loading of problems from the database, the running of said problems
and the eventual storage of their statistics in the database.
"""
import json
import logging
from subprocess import PIPE, Popen
from pathlib import Path

from done_soon.data_generation import db

solver_logger = logging.getLogger("generate_data.worker.solver")
solver_logger.setLevel(logging.DEBUG)

def solve_problem(problem: db.datastructs.Problem, data_dir: Path, mode: str,
                  executable: Path = 'minizinc', time_limit: int = 7200000,
                  save_percentages: list[int] = None,
                  solver: str = 'org.chuffed.modded-chuffed') -> db.datastructs.Problem:
    """
    Runs a given `problem` in MiniZinc. By default it uses our modified chuffed
    solver (must first be compiled and then configured in MiniZinc). It has a time
    limit (TL) and saves all the output features at certain `save_points` percentages
    of that TL.

    Args:
        problem:
            Object with all details regarding a problem instance.
        data_dir:
            Path to the Problems directory
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
                 str(time_limit), '--json-stream', '--output-time', '-r', 42]

    if problem.dzn is not None:
        command = [executable, data_dir / problem.mzn,
                   data_dir / problem.dzn] + exec_args
    else:
        command = [executable, data_dir / problem.mzn] + exec_args
    proc = Popen(command, stdout=PIPE, stderr=PIPE)

    timed_out_comment_found = False
    was_error = False

    # process output line-by-line
    for line in proc.stdout:
        if line == b'\n':
            continue
        try:
            jsonified_line = json.loads(line)
        except json.JSONDecodeError as exc:
            solver_logger.debug("JSON Decode Error: %s, line: %s", exc.msg, line)
            continue
        else:
            match jsonified_line['type'], mode:
                case 'solution', 'label':
                    problem.time_to_solution = jsonified_line['time']
                case 'comment', 'label':
                    if jsonified_line['comment'] == '% Time limit exceeded!':
                        timed_out_comment_found = True
                case 'statistics', 'features':
                    elapsed_time = jsonified_line['statistics']['search_time']
                    if _reached_save_point(elapsed_time, time_limit, save_percentages, save_idx):
                        # made it to a save point
                        save_idx += 1
                        snapshot = db.datastructs.StatisticsSnapshot(
                            elapsed_time/time_limit, jsonified_line['statistics'])
                        problem.statistics.append(snapshot)
                case 'error', _:
                    solver_logger.debug("Solver error (mzn: %s, dzn: %s): %s", problem.mzn, problem.dzn, line)
                    was_error = True

    proc.wait()

    if mode == 'label' and not timed_out_comment_found:
        problem.solved = True

    if was_error:
        solver_logger.error("At least one solver error occured when processing: (mzn: %s, dzn: %s)", problem.mzn, problem.dzn)
        raise RuntimeError(f"Solver error (mzn: {problem.mzn}, dzn: {problem.dzn}), problem could not run")

    return problem


def _reached_save_point(
        elapsed: float, timeout: int, save_percentages: list[int], save_idx: int) -> bool:
    """
    Whenever MiniZinc reaches a percentage of the TL that we want to save
    """
    if save_idx == len(save_percentages):  # no more points to save (reached end of the list)
        return False
    percentage_time_elapsed = elapsed / (timeout / 1000)  # timeout in ms
    save_point_percentage = save_percentages[save_idx] / 100

    return percentage_time_elapsed >= save_point_percentage

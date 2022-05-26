import os
from sys import path
import time
import logging

from dataclasses import dataclass, field
from subprocess import Popen, DEVNULL, PIPE, run
from typing import List, Dict


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


if __name__ == '__main__':
    print(run_problem('tests/resources/test.mzn', 'tests/resources/test.dzn', save_points=[0]))
    print(run_problem('tests/resources/test.mzn', 'tests/resources/test_fail.dzn', save_points=[0]))
    run_problem('problems/2DBinPacking/2DPacking.mzn', 'problems/2DBinPacking/class_1/Class1_100_1.dzn', save_points=[0, 0.1, 0.2, 0.3])
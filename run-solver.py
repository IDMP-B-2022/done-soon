import os
from sys import path, stderr
import time

from dataclasses import dataclass
from subprocess import Popen, PIPE
from typing import List

@dataclass
class #TODO

def run(executable: path, problem_instance: str, options: str = '', timeout: int=7200,
            save_points: List(int)=[5, 10, 15, 20]) -> bool:
    exec_exists = os.path.exists(executable)
    prob_exists = os.path.exists(problem_instance)

    if not exec_exists or not prob_exists:
        print(f'executable exists: {exec_exists} ({executable}), \
                problem exists: {prob_exists} ({problem_instance})', file=stderr)
        return False

    next_save = save_points.pop(0)
    command = f'{executable} {problem_instance}'
    proc = Popen()
    start_time = time.time()

    for line in proc.stdout:
        elapsed = time.time() - start_time
        if elapsed / timeout > next_save / 100:
            # save
            next_save = save_points.pop(0)

    if proc.returncode != 0:
        print('Did not reach timeout successfully')

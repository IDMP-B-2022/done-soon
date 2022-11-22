from pathlib import Path
import pytest

from done_soon.data_generation.data_gen_worker import pre_run_error_checks, per_problem_error_checks


def test_bad_solver():
    with pytest.raises(FileNotFoundError):
        pre_run_error_checks('minizinc', 'solver-does-not-exist', Path('resources'))


def test_bad_executable():
    with pytest.raises(FileNotFoundError):
        pre_run_error_checks('bad-minizinc', 'some-solver', Path('resources'))


def test_bad_model(test_problem_object_mzn_doesnt_exist):
    with pytest.raises(FileNotFoundError):
        per_problem_error_checks(test_problem_object_mzn_doesnt_exist, Path('resources'))


def test_bad_data(test_problem_object_dzn_doesnt_exist):
    with pytest.raises(FileNotFoundError):
        per_problem_error_checks(test_problem_object_dzn_doesnt_exist, Path('resources'))

from pathlib import Path
import pytest

from done_soon.data_generation.solve_problem import solve_problem


def test_run_color_aus_map(test_problem_object_mzn_and_dzn):
    assert solve_problem(test_problem_object_mzn_and_dzn, Path('resources'), 'label').solved


def test_fail_run_color_aus_map(test_problem_object_mzn_and_fail_dzn):
    assert solve_problem(test_problem_object_mzn_and_fail_dzn, Path('resources'), 'label').solved


def test_many_outputs(test_problem_object_mzn_and_dzn):
    assert len(solve_problem(test_problem_object_mzn_and_dzn, Path('resources'),
               'label', save_percentages=[0, 0.001, 0.002, 0.003]).output) == 4


def test_run_color_aus_map_normal_chuffed(test_problem_object_mzn_and_dzn):
    assert solve_problem(test_problem_object_mzn_and_dzn, Path('resources'), 'label', solver='chuffed').solved


# def test_chuffed_long_problem():
#     assert run_problem('problems/2DBinPacking/2DPacking.mzn', 'problems/2DBinPacking/class_1/Class1_100_1.dzn').solved

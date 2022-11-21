from data_generation.run_solver import run_problem
import pytest


def test_run_color_aus_map():
    assert run_problem('tests/resources/test.mzn', 'tests/resources/test.dzn').solved

def test_fail_run_color_aus_map():
    assert not run_problem('tests/resources/test.mzn', 'tests/resources/test_fail.dzn').solved

def test_many_outputs():
    assert len(run_problem('tests/resources/test.mzn', 'tests/resources/test.dzn', save_percentages=[0, 0.001, 0.002, 0.003]).output) == 4

def test_run_color_aus_map_normal_chuffed():
    assert run_problem('tests/resources/test.mzn', 'tests/resources/test.dzn', solver='chuffed').solved

def test_bad_solver():
    with pytest.raises(FileNotFoundError):
        run_problem('tests/resources/test.mzn', 'tests/resources/test.dzn', solver="does-not-exist")

def test_bad_model():
    with pytest.raises(FileNotFoundError):
        run_problem('tests/resources/test-does-not-exist.mzn', 'tests/resources/test.dzn')

def test_bad_data():
    with pytest.raises(FileNotFoundError):
        run_problem('tests/resources/test.mzn', 'tests/resources/test-does-not-exist.dzn')


# def test_chuffed_long_problem():
#     assert run_problem('problems/2DBinPacking/2DPacking.mzn', 'problems/2DBinPacking/class_1/Class1_100_1.dzn').solved

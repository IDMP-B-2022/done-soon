from data_generation.run_solver import run_problem

def test_run_color_aus_map():
    assert run_problem('tests/resources/test.mzn', 'tests/resources/test.dzn').solved

def test_fail_run_color_aus_map():
    assert not run_problem('tests/resources/test.mzn', 'tests/resources/test_fail.dzn').solved

def test_many_outputs():
    assert len(run_problem('tests/resources/test.mzn', 'tests/resources/test.dzn', save_points=[0, 0.001, 0.002, 0.003]).results) == 4

# def test_chuffed_long_problem():
#     assert run_problem('problems/2DBinPacking/2DPacking.mzn', 'problems/2DBinPacking/class_1/Class1_100_1.dzn').solved
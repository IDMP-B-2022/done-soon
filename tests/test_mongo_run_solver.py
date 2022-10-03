import mongomock
from data_generation.run_solver import StatisticsSnapshot, mark_id_as_completed, Problem, update_result_in_db
import dataclasses
import pytest

@pytest.fixture
def problem():
    return Problem(1, 'none.mzn', 'none.dzn', True, 100, 'SAT', [StatisticsSnapshot(50, {'test': 0}), StatisticsSnapshot(50, {'test': 0})])

@pytest.fixture
def mock_todo_db(problem):
    db = mongomock.MongoClient().db
    todo = db.todo
    problems = [dataclasses.asdict(problem)]
    for prob in problems:
        todo.insert_one(prob)

    return db

def test_mark_id_as_completed_label(mock_todo_db):
    db = mock_todo_db
    
    for item in db.todo.find({}):
        mark_id_as_completed(db, item, 'label')
    
    for found in db.todo.find({}):
        assert found['generated_label']

def test_mark_id_as_completed_features(mock_todo_db):
    db = mock_todo_db
    
    for item in db.todo.find({}):
        mark_id_as_completed(db, item, 'features')
    
    for found in db.todo.find({}):
        assert found['generated_features']

def test_insert_problem_results(mock_todo_db, problem):  
    for item in mock_todo_db.todo.find({}):
        update_result_in_db(mock_todo_db, item['_id'], dataclasses.asdict(problem))
    
    for found in mock_todo_db.todo.find({}):
        assert found['statistics'] == dataclasses.asdict(problem)

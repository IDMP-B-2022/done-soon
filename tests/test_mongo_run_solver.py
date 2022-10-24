"""
Tests for the run_solver script and its interactions with MongoDB
"""
import dataclasses

from done_soon.data_generation import db


def test_mark_id_as_completed_label(mock_todo_db):
    database = mock_todo_db

    for item in database.todo.find({}):
        db.functions.mark_id_as_completed(db, item, 'label')

    for found in database.todo.find({}):
        assert found['generated_label']


def test_mark_id_as_completed_features(mock_todo_db):
    database = mock_todo_db

    for item in database.todo.find({}):
        db.functions.mark_id_as_completed(db, item, 'features')

    for found in database.todo.find({}):
        assert found['generated_features']


def test_insert_problem_results(mock_todo_db, problem):
    db.functions.update_result(
        mock_todo_db, dataclasses.asdict(problem))

    for found in mock_todo_db.todo.find({}):
        assert found['statistics'] == dataclasses.asdict(problem)


def test_load_problem_to_dataclass(mock_todo_db_with_problem_no_dzn):
    next_problem = db.functions.read_next_problem(
        mock_todo_db_with_problem_no_dzn, 'label')
    assert next_problem is not None

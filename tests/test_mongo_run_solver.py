"""
Tests for the run_solver script and its interactions with MongoDB
"""
import dataclasses

from ..done_soon.data_generation.db_functions import (
    mark_id_as_completed, read_next_problem_from_db, update_result_in_db)


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
    update_result_in_db(
        mock_todo_db, dataclasses.asdict(problem))

    for found in mock_todo_db.todo.find({}):
        assert found['statistics'] == dataclasses.asdict(problem)


def test_load_problem_to_dataclass(mock_todo_db_with_problem_no_dzn):
    next_problem = read_next_problem_from_db(
        mock_todo_db_with_problem_no_dzn, 'label')
    assert next_problem is not None

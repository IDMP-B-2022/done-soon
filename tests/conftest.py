import dataclasses

import mongomock
import pytest

from done_soon.data_generation import db


@pytest.fixture(name='problem')
def fixture_problem():
    """
    Provides an example problem to insert into a mock DB
    """
    return db.datastructs.Problem(
        1,
        'none.mzn',
        'none.dzn',
        True, 100,
        'SAT',
        [db.datastructs.StatisticsSnapshot(50, {'test': 0}),
         db.datastructs.StatisticsSnapshot(50, {'test': 0})])


@pytest.fixture(name='problem_no_dzn')
def fixture_problem_no_dzn():
    """
    Example problem with no .dzn/data file present
    """
    return db.datastructs.Problem(
        1,
        'none.mzn',
        None, True,
        100, 'SAT',
        [db.datastructs.StatisticsSnapshot(50, {'test': 0}),
         db.datastructs.StatisticsSnapshot(50, {'test': 0})])


@pytest.fixture
def problem_todo_info_no_dzn():
    return {
        "mzn": 'some_prob.mzn',
        "dzn": None,
        "generated_features": False,
        "generated_label": False,
        "claimed_features_generation": False,
        "claimed_label_generation": False
    }


def build_mock_db(to_insert, db_name):
    database = mongomock.MongoClient().db
    collection = database[f'{db_name}']
    for prob in to_insert:
        print(type(prob))
        collection.insert_one(prob)

    return database


@pytest.fixture
def mock_todo_db(problem):
    database = build_mock_db([dataclasses.asdict(problem)], 'problems')

    return database


@pytest.fixture
def mock_todo_db_with_problem_no_dzn(problem_no_dzn):
    database = build_mock_db([dataclasses.asdict(problem_no_dzn)], 'problems')

    return database

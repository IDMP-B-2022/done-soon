import dataclasses

import mongomock
import pytest

from ..done_soon.data_generation.db_datastructs import (Problem,
                                                        StatisticsSnapshot)


@pytest.fixture(name='problem')
def fixture_problem():
    """
    Provides an example problem to insert into a mock DB
    """
    return Problem(
        1,
        'none.mzn',
        'none.dzn',
        True, 100,
        'SAT',
        [StatisticsSnapshot(50, {'test': 0}), StatisticsSnapshot(50, {'test': 0})])


@pytest.fixture(name='problem_no_dzn')
def fixture_problem_no_dzn():
    """
    Example problem with no .dzn/data file present
    """
    return Problem(
        1,
        'none.mzn',
        None, True,
        100, 'SAT',
        [StatisticsSnapshot(50, {'test': 0}), StatisticsSnapshot(50, {'test': 0})])


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
    db = mongomock.MongoClient().db
    collection = db[f'{db_name}']
    for prob in to_insert:
        print(type(prob))
        collection.insert_one(prob)

    return db


@pytest.fixture
def mock_todo_db(problem):
    db = build_mock_db([dataclasses.asdict(problem)], 'problems')

    return db


@pytest.fixture
def mock_todo_db_with_problem_no_dzn(problem_no_dzn):
    db = build_mock_db([dataclasses.asdict(problem_no_dzn)], 'problems')

    return db

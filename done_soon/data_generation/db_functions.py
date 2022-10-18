def read_next_problem_from_db(database, features_or_label):
    """
    Reads the next problem from a problems collection from the mongo `db`.
    The method `find_one_and_update(...)` blocks other processes from
    reading the same problem before the current process 'claims' it.
    """
    problems = database.problems  # empty problems collection if didn't exist
    found = problems.find_one_and_update(
        {f'claimed_{features_or_label}_generation': False},
        {'$set': {f'claimed_{features_or_label}_generation': True}}
    )

    return found

def mark_id_as_completed(database, problem, features_or_label):
    problems = database.problems
    problems.find_one_and_update(
        {'_id': problem._id},
        {'$set': {f'generated_{features_or_label}': True}}
    )

def update_result_in_db(database, problem):
    collected = database.problems
    collected.update_one(
        {'_id': problem._id},
        {'$set':
            {
                'statistics': problem.statistics,
                'time_to_solution': problem.time_to_solution,
                'solved': problem.solved,
                'type': problem.type
            }
        },
        upsert = True
    )
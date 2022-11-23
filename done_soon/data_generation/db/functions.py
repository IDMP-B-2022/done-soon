import dataclasses

def read_next_problem(database, features_or_label):
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

def mark_id_as_completed(database, problem, features_or_label, error=False):
    problems = database.problems
    problems.find_one_and_update(
        {'_id': problem.id},
        {'$set': {f'generated_{features_or_label}': True,}}
    )
    if error:
        problems.find_one_and_update(
        {'_id': problem.id},
        {'$set': {f'error': True,}}
    )

def update_result(database, problem):
    collected = database.problems
    collected.update_one(
        {'_id': problem.id},
        {'$set':
            {
                'statistics': [dataclasses.asdict(stat) for stat in problem.statistics],
                'time_to_solution': problem.time_to_solution,
                'solved': problem.solved,
                'type': problem.type
            }
        },
        upsert = True
    )
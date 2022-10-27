"""
At one point the db structure had two collections:
collected_data and todo. This was an over engineered
solution so this script merges them. It probably isn't
needed any longer, but just in case an old dump of the
data has the old structure, you might use this script
to update it to the newer structure.
"""

import pymongo


def main():
    # Replace the uri string with your MongoDB deployment's connection string.
    conn_str = "mongodb://admin:test@localhost/"

    # set a 5-second connection timeout
    mongo_client = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=5000)
    db = mongo_client.done_soon
    todo = db.todo
    collected_data = db.collected_data
    problems = db.problems
    problems.create_index(
                [("mzn", pymongo.ASCENDING), ("dzn", pymongo.ASCENDING)], unique=True)

    for prob_todo in todo.find():
        collected = collected_data.find_one({"_id": prob_todo['_id']})

        merged = {
            "_id": prob_todo["_id"],
            "mzn": prob_todo["mzn"],
            "dzn": prob_todo["dzn"],
            "generated_features": prob_todo["generated_features"],
            "generated_label": prob_todo["generated_label"],
            "claimed_features_generation": prob_todo["claimed_features_generation"],
            "claimed_label_generation": prob_todo["claimed_label_generation"],
            "type": collected["type"] if collected else None,
            "time_to_solution": collected["time_to_solution"] if collected else None,
            "time_limit": 72000000,

            "solved": collected["solved"] if collected else False,
            "statistics": []
        }
        problems.insert_one(merged)


if __name__ == "__main__":
    main()

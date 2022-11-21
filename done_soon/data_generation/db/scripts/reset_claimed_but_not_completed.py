"""
If the machine crashes or the process is halted
for any other reason, the entries in the database
that were being solved have been marked as "claimed"
but have not been solved, so their claimed flags
should be reset, and statistics cleared.
"""

import pymongo


def main():
    # Replace the uri string with your MongoDB deployment's connection string.
    conn_str = "mongodb://admin:test@localhost/"

    # set a 5-second connection timeout
    mongo_client = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=5000)
    db = mongo_client.done_soon
    problems = db.problems

    MODES = ["label", "features"]

    matches = problems.find({
        "$or": [
            {f"claimed_{mode}_generation": True, f"generated_{mode}": False} for mode in MODES]})
    print(f"There are {len(list(matches))} documents which have claimed and "
          "not completed either label or feature generation.")

    result = problems.update_many(
        {
            "claimed_label_generation": True,
            "generated_label": False
        },
        {"$set": {
            "claimed_label_generation": False,
            "type": None,
            "time_to_solution": None
            }
         }
    )
    print(f"Updated {result.matched_count} documents with unfinished label generation.")

    result = problems.update_many(
        {
            "claimed_features_generation": True,
            "generated_features": False
        },
        {"$set": {
            "claimed_features_generation": False,
            "statistics": list(),
            }
         }
    )
    print(f"Updated {result.matched_count} documents with unfinished feature generation.")



if __name__ == "__main__":
    main()

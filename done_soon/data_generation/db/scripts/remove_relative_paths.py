"""
Relative paths make coding difficult. Just use problem names
instead. This script updates an existing db to do that.
"""
import re
import pymongo


def main():
    # Replace the uri string with your MongoDB deployment's connection string.
    conn_str = "mongodb://admin:test@localhost/"

    # set a 5-second connection timeout
    mongo_client = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=5000)
    db = mongo_client.done_soon
    problems = db.problems

    relative_path_regex = re.compile(r"\.\.\/problems\/")

    matches = problems.find({
        "$or": [{"mzn": {
            "$regex": relative_path_regex
        }},
            {"dzn": {
                "$regex": relative_path_regex
            }}]
    })
    print(f"{len(list(matches))} paths to update")

    for file in ["mzn", "dzn"]:
        selection = problems.find({file: {"$regex": relative_path_regex}})
        for prob in selection:
            stripped_string = prob[file][12:]
            problems.update_one(
                {"_id": prob["_id"]},
                {"$set": {file: stripped_string}}
        )


if __name__ == "__main__":
    main()

import argparse
import dataclasses
import os
from pathlib import Path

import bson
import pymongo
from pymongo import errors
from rich.progress import Progress

from done_soon.data_generation.db.datastructs import Problem

# Replace the uri string with your MongoDB deployment's connection string.
conn_str = "mongodb://admin:test@localhost/"

# set a 5-second connection timeout
mongo_client = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=5000)


def insert(client, mzn, dzn=None):
    db = client['done_soon']
    collection = db['problems']
    problem = Problem(bson.ObjectId(), mzn, dzn)
    result = collection.insert_one(dataclasses.asdict(problem))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--data', type=Path,
                        help="Path to Problems folder", required=True)
    args = parser.parse_args()

    with Progress() as progress:
        all_problems = os.listdir(args.data)
        outerbar = progress.add_task("Loading problem", total=len(all_problems))
        innerbar = progress.add_task("Loading problem instance")

        for item in all_problems:
            progress.update(outerbar, advance=1)
            if os.path.isfile(os.path.join(args.data, item)):
                continue

            dir_path = os.path.join(args.data, item)
            mzn_files = list(os.listdir(dir_path))
            dzn_files = list(os.listdir(dir_path + "/data"))

            mzn_files = [f for f in mzn_files if f[-4:]
                         == '.mzn' and not f.startswith(".")]
            dzn_files = [f for f in dzn_files if f[-4:] == '.dzn']

            db = mongo_client['done_soon']
            collection = db['problems']
            collection.create_index(
                [("mzn", pymongo.ASCENDING), ("dzn", pymongo.ASCENDING)], unique=True)

            progress.update(innerbar, total=len(mzn_files) if len(dzn_files) == 0 else len(dzn_files))

            for mzn_file in mzn_files:
                mzn_path = None
                dzn_path = None
                try:
                    if len(dzn_files) == 0:
                        progress.update(innerbar, advance=1)
                        mzn_path = os.path.join(item, mzn_file)
                        insert(mongo_client, mzn_path)
                    else:
                        for dzn_file in dzn_files:
                            progress.update(innerbar, advance=1)
                            mzn_path = os.path.join(item, mzn_file)
                            dzn_path = os.path.join(item, "data" + dzn_file)
                            insert(mongo_client, mzn_path, dzn_path)
                except errors.DuplicateKeyError:
                    progress.update(
                        innerbar,
                        description=f"Already added to db: {mzn_path}{' : ' if dzn_path else ''}{dzn_path}")
            
            progress.update(innerbar, completed=0)

if __name__ == "__main__":
    main()

import os
import pymongo
from pymongo import errors
from tqdm import tqdm

# Replace the uri string with your MongoDB deployment's connection string.
conn_str = "mongodb://admin:test@localhost/"

# set a 5-second connection timeout
mongo_client = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=5000)


def insert(client, mzn, dzn=None):
    db = client['done_soon']
    collection = db['todo']
    result = collection.insert_one({
        "mzn": mzn,
        "dzn": dzn,
        "generated_features": False,
        "generated_label": False,
        "claimed_features_generation": False,
        "claimed_label_generation": False
    })
    return result


for item in (outerbar := tqdm(  os.listdir("../problems"),
                                position=0,
                                desc="Problem")):
    if os.path.isfile(os.path.join("../problems", item)):
        continue

    dir_path = os.path.join("../problems", item)
    subfiles = (list(os.walk(dir_path)))
    mzn_files = list(os.listdir(dir_path))
    dzn_files = list(os.listdir(dir_path + "/data"))

    mzn_files = [f for f in mzn_files if f[-4:] == '.mzn' and not f.startswith(".")]
    dzn_files = [f for f in dzn_files if f[-4:] == '.dzn']

    db = mongo_client['done_soon']
    collection = db['todo']
    collection.create_index([("mzn", pymongo.ASCENDING), ("dzn", pymongo.ASCENDING)], unique=True)

    for mzn_file in (innerbar := tqdm(  mzn_files,
                                        position=1,
                                        leave=False,
                                        desc="Instance")):
        mzn_path = None
        dzn_path = None
        try:
            if len(dzn_files) == 0:
                mzn_path = os.path.join(dir_path, mzn_file)
                insert(mongo_client, mzn_path)
            else:
                for dzn_file in dzn_files:
                    mzn_path = os.path.join(dir_path, mzn_file)
                    dzn_path = os.path.join(dir_path, "data/" + dzn_file)
                    insert(mongo_client, mzn_path, dzn_path)
        except errors.DuplicateKeyError as e:
            outerbar.set_description(f"Already added to db: {mzn_path}{' : ' if dzn_path else ''}{dzn_path}")


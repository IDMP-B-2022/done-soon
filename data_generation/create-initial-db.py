import os
import pymongo

# Replace the uri string with your MongoDB deployment's connection string.
conn_str = "mongodb+srv://admin:test@localhost:27017/"
# set a 5-second connection timeout
mongo_client = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=5000)


def insert(client, mzn, dzn=None):
    db = client['done_soon']
    collection = db['todo']
    result = collection.insert_one({
        "mzn": mzn,
        "dzn": dzn
    })
    return result


for item in os.listdir("../problems"):
    if os.path.isfile(os.path.join("../problems", item)):
        continue

    dir_path = os.path.join("../problems", item)
    subfiles = (list(os.walk(dir_path)))
    mzn_files = list(os.listdir(dir_path))
    dzn_files = list(os.listdir(dir_path + "/data"))

    mzn_files = [f for f in mzn_files if f[-4:] == '.mzn' and not f.startswith(".")]
    dzn_files = [f for f in dzn_files if f[-4:] == '.dzn']

    for mzn_file in mzn_files:
        if len(dzn_files) == 0:
            path = os.path.join(dir_path, mzn_file)
            insert(mongo_client, path)
        else:
            for dzn_file in dzn_files:
                mzn_path = os.path.join(dir_path, mzn_file)
                dzn_path = os.path.join(dir_path, "data/" + dzn_file)
                insert(mongo_client, mzn_path, dzn_path)


import os
import json
from collections import defaultdict
from subprocess import Popen, PIPE
import sqlite3


total_amount_of_problems = 0
count_of_methods = defaultdict(int)
count_of_variables = defaultdict(int)
types_per_model = {}

db = sqlite3.connect('output.db')
table = """ CREATE TABLE todo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mzn VARCHAR(255) not null,
        dzn VARCHAR(255)
    ); """

cursor = db.cursor()
cursor.execute(table)

for item in os.listdir("../problems"):
    if os.path.isfile(os.path.join("../problems", item)):
        continue

    dir_path = os.path.join("../problems", item)
    subfiles = (list(os.walk(dir_path)))
    mzn_files = list(os.listdir(dir_path))
    dzn_files = list(os.listdir(dir_path + "/data"))

    mzn_files = [f for f in mzn_files if f[-4:] == '.mzn' and not f.startswith(".")]
    dzn_files = [f for f in dzn_files if f[-4:] == '.dzn']

    for mzn in mzn_files:
        if len(dzn_files) == 0:
            sql = ''' INSERT INTO todo(mzn) VALUES(?) '''
            path = os.path.join(dir_path, mzn)
            cursor.execute(sql, (path,))
            db.commit()
        else:
            for dzn in dzn_files:
                sql = ''' INSERT INTO todo(mzn, dzn) VALUES(?, ?) '''
                mzn_path = os.path.join(dir_path, mzn)
                dzn_path = os.path.join(dir_path, "data/" + dzn)
                cursor.execute(sql, (mzn_path, dzn_path))
                db.commit()

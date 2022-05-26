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


#     # Now to check the type of problem.
#     for model in mzn_files:
#         process = Popen(["minizinc", "--model-interface-only", os.path.join(dir_path, model)], stdout=PIPE)
#         (output, error) = process.communicate()
#         if error:
#             print("ERROR: {}".format(error))
#             exit(0)
#         try:
#             interface = json.loads(output)
#             count_of_methods[interface['method']] += contributes
#             interface = {**interface['input'], **interface['output']}
#
#
#             int_vars = False
#             bool_vars = False
#             types_per_model[model] = set()
#             for key in interface.keys():
#                 if key in ["type", "method", "has_output_item", "included_files", "globals"]:
#                     continue
#                 type_of_variable = interface[key]['type']
#                 if type_of_variable == 'int':
#                     int_vars = True
#                 if type_of_variable == 'bool' or type_of_variable == 'boolean':
#                     bool_vars = True
#                 types_per_model[model].add(type_of_variable)
#
#             if int_vars and bool_vars:
#                 count_of_variables['both'] += contributes
#             elif int_vars:
#                 count_of_variables['int'] += contributes
#             elif bool_vars:
#                 count_of_variables['bool'] += contributes
#             else:
#                 print(model, interface)
#                 count_of_variables['weird'] += contributes
#
#
#
#         except ValueError as e:
#             print("ERROR: apparently JSON cant be loaded for model {}?".format(model))
#             exit(0)
#
# # Because serializing sets is just too hard...........
# # Attribution: https://stackoverflow.com/questions/8230315/how-to-json-serialize-sets
# # In order to avoid legal issues :upsidedown:
# class SetEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, set):
#             return list(obj)
#         return json.JSONEncoder.default(self, obj)
#
#
# with open('result.json', 'w') as f:
#     f.write(json.dumps({
#         'total_number_of_problems': total_amount_of_problems,
#         'count_per_method': count_of_methods,
#         'count_per_variable': count_of_variables,
#         'types_per_mode': types_per_model
#     }, cls=SetEncoder))

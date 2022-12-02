import os
import json
from collections import defaultdict
from subprocess import Popen, PIPE
import pymongo
from pymongo.database import Database
from rich import print
from rich.progress import Progress, MofNCompleteColumn, TextColumn, BarColumn


total_amount_of_problems = 0
count_of_methods = defaultdict(int)
count_of_variables = defaultdict(int)
types_per_model = {}

with Progress(TextColumn("{task.description}"), BarColumn(), MofNCompleteColumn()) as progress:
    all_problem_sets = os.listdir(".")
    problem_task = progress.add_task("Problem", total=len(all_problem_sets))

    for item in all_problem_sets:

        if os.path.isfile(os.path.join(".", item)):
            progress.update(problem_task, advance=1)
            continue

        dir_path = os.path.join(".", item)
        subfiles = (list(os.walk(dir_path)))
        mzn_files = list(os.listdir(dir_path))
        dzn_files = list(os.listdir(dir_path + "/data"))

        mzn_files = [f for f in mzn_files if f[-4:]
                     == '.mzn' and not f.startswith(".")]
        dzn_files = [f for f in dzn_files if f[-4:] == '.dzn']

        if len(dzn_files) == 0:
            # Problems are based on mzn => count the amount of mzn files!
            total_amount_of_problems += len(mzn_files)
            contributes = 1
        else:
            # It's the dzn files that count! But multiply by amount of mzn files
            # for the few instances where multiple models for the same problem exist.
            # (see for example the still_life problem)
            total_amount_of_problems += (len(mzn_files) * len(dzn_files))
            contributes = len(dzn_files)

        error_list = []

        conn_str = f"mongodb://localhost:27017/"
        mongo_client = pymongo.MongoClient(
            conn_str, serverSelectionTimeoutMS=5000)
        database = mongo_client['done_soon']['problems']

        model_task = progress.add_task("Model", total=len(mzn_files))

        # Now to check the type of problem.
        for model in mzn_files:

            try:
                with open(os.path.join(dir_path, model), 'r') as f:
                    text = f.read()

                    sat = "satisfy" in text
                    opt = "minimize" in text or "maximize" in text

                    # takes care of the defaulting to SAT
                    problem_type = "OPT" if opt else "SAT"

                    if len(dzn_files) != 0:
                        for dzn in dzn_files:
                            matched = database.update_one({
                                "dzn": dir_path[2:] + "/data/" + dzn,
                                "mzn": dir_path[2:] + "/" + model
                            }, {"$set": {"problem_type": problem_type}}).matched_count

                    else:
                        matched = database.update_one({
                            "dzn": None,
                            "mzn": dir_path[2:] + "/" + model
                        }, {"$set": {"problem_type": problem_type}}).matched_count

            # process = Popen(["minizinc", "--model-interface-only", ], stdout=PIPE)
            # (output, error) = process.communicate()
            # if error:
            #     print("ERROR: {}".format(error))
            #     exit(0)
            # try:
            #     interface = json.loads(output)
            #     count_of_methods[interface['method']] += contributes
            #     interface = {**interface['input'], **interface['output']}

            #     int_vars = False
            #     bool_vars = False
            #     types_per_model[model] = set()
            #     for key in interface.keys():
            #         if key in ["type", "method", "has_output_item", "included_files", "globals"]:
            #             continue
            #         type_of_variable = interface[key]['type']
            #         if type_of_variable == 'int':
            #             int_vars = True
            #         if type_of_variable == 'bool' or type_of_variable == 'boolean':
            #             bool_vars = True
            #         types_per_model[model].add(type_of_variable)

            #     if int_vars and bool_vars:
            #         count_of_variables['both'] += contributes
            #     elif int_vars:
            #         count_of_variables['int'] += contributes
            #     elif bool_vars:
            #         count_of_variables['bool'] += contributes
            #     else:
            #         print(model, interface)
            #         count_of_variables['weird'] += contributes

            except ValueError as e:
                print("ERROR: JSON cant be loaded for model {}?".format(model))
                error_list.append(model)

            progress.update(model_task, advance=1)
        progress.remove_task(model_task)
        progress.update(problem_task, advance=1)

        # print(f"Errored on {len(error_list)}")

# Because serializing sets is just too hard...........
# Attribution: https://stackoverflow.com/questions/8230315/how-to-json-serialize-sets
# In order to avoid legal issues :upsidedown:


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


# with open('result.json', 'w') as f:
#     f.write(json.dumps({
#         'total_number_of_problems': total_amount_of_problems,
#         'count_per_method': count_of_methods,
#         'count_per_variable': count_of_variables,
#         'types_per_mode': types_per_model
#     }, cls=SetEncoder))

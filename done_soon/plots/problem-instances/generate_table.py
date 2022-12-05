import re
import pymongo

conn_str = "mongodb://localhost"
mongo_client = pymongo.MongoClient(conn_str, port=27017)
problems = mongo_client.done_soon.problems

base_filter = {"error": {"$ne": True}}

non_miplib_regex = re.compile(r"^(?!miplib)")
miplib_regex = re.compile(r"^miplib")

num_non_miplib = problems.count_documents(
    non_miplib_filter := {'mzn': non_miplib_regex} | base_filter)
num_miplib = problems.count_documents(
    miplib_filter := {'mzn': miplib_regex} | base_filter)

print(  f"Challenges and Benchmarks: {num_non_miplib}, "
        f"MIPLIB: {num_miplib}, \ttotal: {num_non_miplib + num_miplib}")

prob_type_res = {}
for problem_type in ["OPT", "SAT"]:
    problem_type_filter = {'problem_type': problem_type}
    num_TYPE_non_miplib = problems.count_documents(
        {'mzn': non_miplib_regex} | base_filter | problem_type_filter)
    num_TYPE_miplib = problems.count_documents(
        {'mzn': miplib_regex} | base_filter | problem_type_filter)
    prob_type_res[problem_type] = {
        'non_miplib': num_TYPE_non_miplib,
        'miplib': num_TYPE_miplib,
        'total': num_TYPE_non_miplib + num_TYPE_miplib
    }
    print(  f"Challenges and Benchmarks {problem_type}: {num_TYPE_non_miplib}, "
            f"MIPLIB {problem_type}: {num_TYPE_miplib}, \ttotal {problem_type}: {num_TYPE_non_miplib + num_TYPE_miplib}")

time_limit = 7199000
num_solved_before_TL_miplib = problems.count_documents(
    {'time_to_solution': {'$lt': time_limit, '$ne': None}} | miplib_filter)
num_solved_before_TL_non_miplib = problems.count_documents(
    {'time_to_solution': {'$lt': time_limit, '$ne': None}} | non_miplib_filter)
num_solved_before_TL = num_solved_before_TL_miplib + num_solved_before_TL_non_miplib

num_unsolved_after_5TL_miplib = problems.count_documents(
    {'$or': [   {'time_to_solution': {'$gte': 0.05 * time_limit}},
                {'time_to_solution': None},]} | miplib_filter)
num_unsolved_after_5TL_non_miplib = problems.count_documents(
    {'$or': [   {'time_to_solution': {'$gte': 0.05 * time_limit}},
                {'time_to_solution': None},]} | non_miplib_filter)
num_unsolved_after_5TL = num_unsolved_after_5TL_miplib + num_unsolved_after_5TL_non_miplib

num_unsolved_after_TL_miplib = problems.count_documents(
    {'$or': [   {'time_to_solution': {'$gte': time_limit}},
                {'time_to_solution': None},]} | miplib_filter)
num_unsolved_after_TL_non_miplib = problems.count_documents(
    {'$or': [   {'time_to_solution': {'$gte': time_limit}},
                {'time_to_solution': None},]} | non_miplib_filter)
num_unsolved_after_TL = num_unsolved_after_TL_miplib + num_unsolved_after_TL_non_miplib


print(  f"Solved before 2h: {num_solved_before_TL}, unsolved: {num_unsolved_after_TL}, "
        f"\ttotal: {num_solved_before_TL + num_unsolved_after_TL}")

print("LaTeX:")
print(  f"Acquired & {num_non_miplib} & {num_miplib} & {num_non_miplib + num_miplib}\\\\\n"
        f"Solved within \\acrshort{{tl}} & {num_solved_before_TL_non_miplib}"
        f" & {num_solved_before_TL_miplib} & {num_solved_before_TL}\\\\\n"
        f"Unsolved within 5\\% of \\acrshort{{tl}} & {num_unsolved_after_5TL_non_miplib}"
        f" & {num_unsolved_after_5TL_miplib} & {num_unsolved_after_5TL}\\\\\n"
        f"Unsolved within \\acrshort{{tl}}& {num_unsolved_after_TL_non_miplib}"
        f" & {num_unsolved_after_TL_miplib} & {num_unsolved_after_TL}\\\\\\midrule\n"
        f"Satisfiability (SAT) & {prob_type_res['SAT']['non_miplib']} & {prob_type_res['SAT']['miplib']} & {prob_type_res['SAT']['total']}\\\\\n"
        f"Optimization (OPT) & {prob_type_res['OPT']['non_miplib']} & {prob_type_res['OPT']['miplib']} & {prob_type_res['OPT']['total']}\\\\"
)

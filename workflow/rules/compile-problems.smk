import pathlib


include: "unpack-problems.smk"


def match_mzn_dzn(mzn_file, dzn_file):
    print(mzn_file)
    pairs = []
    pairs.append((mzn[1], dzn_files[0][1]))
    return pairs

def aggregate_unpacked_problems(wildcards):
    checkpoint_output = checkpoints.unpack_all_problems.get(**wildcards).output[0]
    checkpoint_path = Path(checkpoint_output)
    # print([x.parent.name for x in checkpoint_path.glob("**/*.mzn")])
    # for mzn in 
    # mzn_files = glob_wildcards(os.path.join(checkpoint_output, "{problem,[\w\-\/]+}.mzn")).problem
    # dzn_files = glob_wildcards(os.path.join(checkpoint_output, "{problem,[\w\-\/]+}.dzn")).problem

    # return expand("blah/{mzn}/{dzn}", match_mzn_dzn, mzn=mzn_files, dzn=dzn_files)


# checkpoint compile_all_problems:
#     input:
#         aggregate_unpacked_problems,
#     output:
#         directory("resources/problems_compiled"),
#     run:
#         print()

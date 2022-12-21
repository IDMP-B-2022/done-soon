import pathlib
import os

include: "download-convert-problems.smk"


# def match_mzn_dzn(mzn_file, dzn_file):
#     print(mzn_file)
#     pairs = []
#     pairs.append((mzn[1], dzn_files[0][1]))
#     return pairs

def aggregate_uncompiled_problems(wildcards):
    checkpoint_output = checkpoints.copy_problems_to_resources.get(**wildcards).output[0]
    problems_path = Path(checkpoint_output)
    compiled_filenames = []
    mzn_list = list(problems_path.glob("**/*.mzn"))
    print(len(mzn_list))
    for i, mzn in enumerate(mzn_list):

        # Prepend resource folder to the path, and prefix filename with problem type
        if i % 500 == 0:
            print(i)
        # print(mzn, mzn.parent)
        if mzn.parent.stem == "satlib":
            compiled_filenames.append(f"{mzn.stem}-NO-MODEL-FILE.fzn")
            continue

        dzn_list = list(mzn.parent.glob("**/*.dzn"))
        if not dzn_list:
            compiled_filenames.append(f"{mzn.stem}-NO-MODEL-FILE.fzn")
        else:
            for dzn in dzn_list:
                compiled_filenames.append(f"{mzn.stem}-{dzn.stem}.fzn")

    return compiled_filenames

checkpoint compile_all_problems:
    input:
        # expand("{mzn}__{dzn}.fzn", )
        aggregate_uncompiled_problems,
    output:
        directory("resources/problems_compiled"),
    run:
        print()

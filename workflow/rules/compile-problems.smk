include: "unpack-problems.smk"


def aggregate_unpacked_problems(wildcards):
    checkpoint_output = checkpoints.unpack_all_problems.get(**wildcards).output[0]
    mzn = glob_wildcards(os.path.join(checkpoint_output, "{problem,[\w\-\/]+}.mzn")).problem
    print([f"{x}.mzn" for x in mzn])


checkpoint compile_all_problems:
    input:
        aggregate_unpacked_problems,
    output:
        directory("resources/problems_compiled"),
    run:
        print()

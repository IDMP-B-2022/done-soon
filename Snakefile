from snakemake.utils import min_version

min_version("7.18.2")

import glob


rule all:
    input:
        "analysis.log",


rule minizinc:
    input:
        "new_problems/problem_sets/{problem}/{model}.mzn",
        "new_problems/problem_sets/{problem}/data/{data}.dzn",
    output:
        "output-{problem}-{model}-{data}.log",
    threads: 1
    shell:
        "minizinc {input} -t 100 | tee {output}"


PROB_NUMBERS = list(range(1, 11))


rule analyze:
    input:
        expand(
            "output-2DBinPacking-2DPacking-Class1_20_{number}.log", number=PROB_NUMBERS
        ),
    output:
        "analysis.log",
    shell:
        "cat {input} > {output}"


rule build_docker:
    input:
        "Dockerfile",
    output:
        "images/test.tar",
    shell:
        "docker buildx build . --target with_python_pip -t test &&"
        "docker save -o images/test.tar test"


rule test_run_docker:
    input:
        "test-input.txt",
        "images/test.tar",
    output:
        "test-output.txt",
    container:
        "images/test.tar"
    shell:
        "touch test-output.txt"


# Utility


rule clean:
    shell:
        "rm -rf new_problems"


rule get_data:
    input:
        "problems/problem_sets/2DBinPacking/data/Class1_20_{number}.dzn",
    output:
        "new_problems/problem_sets/2DBinPacking/data/Class1_20_{number}.dzn",
    shell:
        "cp {input} {output}"


rule get_model:
    input:
        "problems/problem_sets/2DBinPacking/2DPacking.mzn",
    output:
        "new_problems/problem_sets/2DBinPacking/2DPacking.mzn",
    shell:
        "cp {input} {output}"

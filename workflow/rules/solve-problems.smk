rule solve_problem_normal_chuffed:
    input:
        "resources/problems_compiled/{fzn_file}.fzn"
    output:
        temp("temp/problem_output/{fzn_file}-OUTPUT-NORMAL.bson")
    conda:
        "../envs/solve_problem.yaml"
    container:
        "workflow/containers/solve_problem.sif"
    benchmark:
        "benchmarks/solve/{fzn_file}-OUTPUT-NORMAL.tsv"
    shell:
        "minizinc {input} --solver org.chuffed.chuffed -t 7200000 --json-stream --output-time -r 42 | python3 workflow/scripts/ingest_bson.py {output}"


rule solve_problem_stats_chuffed:
    input:
        "resources/problems_compiled/{fzn_file}.fzn"
    output:
        temp("temp/problem_output/{fzn_file}-OUTPUT-STATS.bson")
    conda:
        "../envs/solve_problem.yaml"
    container:
        "workflow/containers/solve_problem.sif"
    benchmark:
        "benchmarks/solve/{fzn_file}-OUTPUT-STATS.tsv"
    shell:
        "minizinc {input} --solver org.chuffed.modded-chuffed -t 7200000 --json-stream --output-time -r 42 | python3 workflow/scripts/ingest_bson.py {output}"


def list_all_bson_files(wildcards):
    checkpoint_output = checkpoints.compile_all_problems.get(**wildcards).output[0]
    fzns = glob_wildcards(f"{checkpoint_output}/{{fzn}}.fzn").fzn
    return expand("temp/problem_output/{fzn}-OUTPUT-{version}.bson", fzn=fzns, version=["NORMAL", "STATS"])


rule solve_all_problems:
    input:
        list_all_bson_files
    output:
        directory("resources/problems_output"),
    shell:
        "cp -r temp/problems_output/. {output}"
rule solve_problem_normal_chuffed:
    input:
        "resources/problems_compiled/{fzn_file}.fzn"
    output:
        "results/problem_output/{fzn_file}-OUTPUT-NORMAL.bson"
    conda:
        "../envs/solve_problem.yaml"
    container:
        "workflow/containers/solve_problem.sif"
    shell:
        "minizinc {input} --solver org.chuffed.chuffed -t 7200000 --json-stream --output-time -r 42 | python3 workflow/scripts/ingest_bson.py {output}"


rule solve_problem_stats_chuffed:
    input:
        "resources/problems_compiled/{fzn_file}.fzn"
    output:
        "results/problem_output/{fzn_file}-OUTPUT-STATS.bson"
    conda:
        "../envs/solve_problem.yaml"
    container:
        "workflow/containers/solve_problem.sif"
    shell:
        "minizinc {input} --solver org.chuffed.modded-chuffed -t 7200000 --json-stream --output-time -r 42 | python3 workflow/scripts/ingest_bson.py {output}"
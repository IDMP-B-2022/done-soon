rule solve_problem_normal_chuffed:
    input:
        "resources/problems_compiled/{fzn_file}.fzn"
    output:
        "resources/problem_output/{fzn_file}-OUTPUT-NORMAL.bson"
    conda:
        "../envs/solve_problem.yaml"
    shell:
        "minizinc {input} --solver org.chuffed.chuffed -t 7200000 --json-stream --output-time -r 42"

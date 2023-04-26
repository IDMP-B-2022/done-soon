include: "compile-problems.smk"


def get_mem_mb(wildcards, attempt):
    """
    Each time the problem is re-attempted, it adds a GB
    to the memory needed.
    """
    return (attempt * 1000) + 1500


rule solve_problem_normal_chuffed:
    input:
        f"{config['base_dir']}/resources/problems_compiled/{{fzn_file}}.fzn",
    output:
        temp(
            f"{config['base_dir']}/temp/problem_output/{{fzn_file}}-OUTPUT-NORMAL.json"
        ),
    conda:
        "../envs/solve_problem.yaml"
    container:
        f"{config['base_dir']}/containers/solve_problem.sif"
    resources:
        mem_mb=get_mem_mb
    benchmark:
        f"{config['base_dir']}/benchmarks/solve/{{fzn_file}}-OUTPUT-NORMAL.tsv"
    log:
        stdout=f"{config['base_dir']}/log/solve/stdout/{{fzn_file}}-OUTPUT-NORMAL.log",
        stderr=f"{config['base_dir']}/log/solve/stderr/{{fzn_file}}-OUTPUT-NORMAL.log",
    shell:
        "(minizinc {input} --solver org.chuffed.chuffed -t 7200000 --json-stream --output-time -r 42 | python3 workflow/scripts/save_solver_output.py {output}) > {log.stdout} 2>{log.stderr}"


rule solve_problem_stats_chuffed:
    input:
        f"{config['base_dir']}/resources/problems_compiled/{{fzn_file}}.fzn",
    output:
        temp(f"{config['base_dir']}/temp/problem_output/{{fzn_file}}-OUTPUT-STATS.json"),
    conda:
        "../envs/solve_problem.yaml"
    container:
        f"{config['base_dir']}/containers/solve_problem.sif"
    resources:
        mem_mb=get_mem_mb
    benchmark:
        f"{config['base_dir']}/benchmarks/solve/{{fzn_file}}-OUTPUT-STATS.tsv"
    log:
        stdout=f"{config['base_dir']}/log/solve/stdout/{{fzn_file}}-OUTPUT-STATS.log",
        stderr=f"{config['base_dir']}/log/solve/stderr/{{fzn_file}}-OUTPUT-STATS.log",
    shell:
        "(minizinc {input} --solver org.chuffed.modded-chuffed -t 7200000 --json-stream --output-time -r 42 | python3 workflow/scripts/save_solver_output.py {output}) > {log.stdout} 2>{log.stderr}"


def list_all_output_files(wildcards):
    checkpoint_output = checkpoints.compile_all_problems.get(**wildcards).output[0]
    fzns = glob_wildcards(f"{checkpoint_output}/{{fzn}}.fzn").fzn
    return expand(
        f"{config['base_dir']}/temp/problem_output/{{fzn}}-OUTPUT-{{version}}.json",
        fzn=fzns,
        version=["NORMAL", "STATS"],
    )


checkpoint solve_all_problems:
    input:
        list_all_output_files,
    output:
        directory(f"{config['base_dir']}/resources/problem_output"),
    shell:
        f"cp -r {config['base_dir']}/temp/problem_output/. {{output}}"

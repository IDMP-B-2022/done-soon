from pathlib import Path

include: "solve-problems.smk"

rule create_features_at_percentile:
    input:
        lambda wildcards: checkpoints.solve_all_problems.get(**wildcards).output[0]
    output: f"{config['base_dir']}/resources/features_at_percentiles.pkl"
    threads: workflow.cores
    shell: "python workflow/scripts/output_to_features_at_percent.py --input_dir {input} --output_filename {output} --num_processes {threads}"
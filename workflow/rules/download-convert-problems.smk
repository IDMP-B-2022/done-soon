rule download_all_problems:
    output:
        temp(directory(f"{config['base_dir']}/temp/problems")),
    conda:
        "../envs/download-convert-problems.yaml"
    threads: workflow.cores
    script:
        "../scripts/download.py"


rule convert_cnf_problems:
    input:
        f"{config['base_dir']}/temp/problems/",
    output:
        temp(directory(f"{config['base_dir']}/temp/converted_satlib/")),
    script:
        "../scripts/convert_cnf.py"


checkpoint copy_problems_to_resources:
    input:
        f"{config['base_dir']}/temp/problems",
        f"{config['base_dir']}/temp/converted_satlib",
    output:
        directory(f"{config['base_dir']}/resources/problems"),
    shell:
        f"cp -r {config['base_dir']}/temp/problems/ {{output}} && cp -r {config['base_dir']}/temp/converted_satlib/. {config['base_dir']}/resources/problems/satlib"

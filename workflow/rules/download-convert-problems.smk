rule download_all_problems:
    output:
        directory("temp/problems"),
    conda:
        "../envs/download-convert-problems.yaml"
    script:
        "../scripts/download.py"


rule convert_cnf_problems:
    input:
        "temp/problems/satlib/cnf"
    output:
        directory("temp/converted_satlib/")
    script:
        "../scripts/convert_cnf.py"


checkpoint copy_problems_to_resources:
    input:
        "temp/problems",
        "temp/converted_satlib"
    output:
        directory("resources/problems")
    shell:
        "cp -r temp/problems/ resources/problems/ && cp -r temp/converted_satlib/. resources/problems/satlib"


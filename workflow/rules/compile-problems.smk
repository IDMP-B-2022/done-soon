import pathlib
import os


include: "download-convert-problems.smk"


def aggregate_uncompiled_problems(wildcards):
    checkpoint_output = checkpoints.copy_problems_to_resources.get(**wildcards).output[
        0
    ]
    problems_path = Path(checkpoint_output)
    compiled_filenames = []
    mzn_list = list(problems_path.glob("**/*.mzn"))
    fzn_temp_dir = f"{config['base_dir']}/temp/problems_compiled/"
    for i, mzn in enumerate(mzn_list):
        # this is a bit of a hack to avoid globbing the satlib folder over and over
        if mzn.parent.stem == "satlib":
            compiled_filenames.append(
                fzn_temp_dir
                + f"PROB-{mzn.parent.stem}-MZN-{mzn.stem}-DZN-NO-MODEL-FILE.fzn"
            )
            continue

        dzn_list = list(mzn.parent.glob("data/*.dzn"))
        if not dzn_list:
            compiled_filenames.append(
                fzn_temp_dir
                + f"PROB-{mzn.parent.stem}-MZN-{mzn.stem}-DZN-NO-MODEL-FILE.fzn"
            )
        else:
            for dzn in dzn_list:
                compiled_filenames.append(
                    fzn_temp_dir
                    + f"PROB-{mzn.parent.stem}-MZN-{mzn.stem}-DZN-{dzn.stem}.fzn"
                )

    return compiled_filenames


checkpoint compile_all_problems:
    input:
        aggregate_uncompiled_problems,
    output:
        directory(f"{config['base_dir']}/resources/problems_compiled"),
    shell:
        f"cp -r {config['base_dir']}/temp/problems_compiled/. {{output}}"


rule compile_problem_no_model:
    input:
        mzn=f"{config['base_dir']}/resources/problems/{{problem}}/{{mzn}}.mzn",
    output:
        fzn = temp(f"{config['base_dir']}/temp/problems_compiled/PROB-{{problem}}-MZN-{{mzn}}-DZN-NO-MODEL-FILE.fzn"),
        ozn = temp(f"{config['base_dir']}/temp/problems_compiled/PROB-{{problem}}-MZN-{{mzn}}-DZN-NO-MODEL-FILE.ozn"),
    benchmark:
        f"{config['base_dir']}/benchmarks/compile/PROB-{{problem}}-MZN-{{mzn}}-DZN-NO-MODEL-FILE.tsv"
    shell:
        "minizinc {input.mzn} --compile --fzn {output.fzn} --ozn {output.ozn} --solver org.chuffed.chuffed"


rule compile_problem:
    input:
        mzn=f"{config['base_dir']}/resources/problems/{{problem}}/{{mzn}}.mzn",
        dzn=f"{config['base_dir']}/resources/problems/{{problem}}/data/{{dzn}}.dzn",
    output:
        fzn=temp(f"{config['base_dir']}/temp/problems_compiled/PROB-{{problem}}-MZN-{{mzn}}-DZN-{{dzn}}.fzn"),
        ozn=temp(f"{config['base_dir']}/temp/problems_compiled/PROB-{{problem}}-MZN-{{mzn}}-DZN-{{dzn}}.ozn"),
    benchmark:
        f"{config['base_dir']}/benchmarks/compile/PROB-{{problem}}-MZN-{{mzn}}-DZN-{{dzn}}.tsv"
    shell:
        "minizinc {input.mzn} {input.dzn} --compile --fzn {output.fzn} --ozn {output.ozn} --solver org.chuffed.chuffed"

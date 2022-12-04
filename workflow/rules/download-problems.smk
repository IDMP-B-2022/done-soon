import json
import os


def find_corresponding_link(wildcards, params):
    with open(f"resources/download/links-{wildcards.source}.json", "r") as in_file:
        links = json.load(in_file)
        for link in links:
            if params.file in link:
                return link


def get_resource_names(source):
    if source == "miplib":
        return [f"temp/miplib/miplib.zip"]
    with open(f"resources/download/links-{source}.json", "r") as in_file:
        return [f"temp/{source}/{os.path.basename(link)}" for link in json.load(in_file)]


rule download_miplib:
    output:
        "temp/miplib/miplib.zip"
    params:
        link = "1n0RZLUdFBW4Nhmdwj02VqW_gG6s8S8I8",
    conda:
        "../envs/download-problems.yaml"
    shell:
        "gdown -O {output} {params.link}"


rule download_individual_problem:
    output:
        temp("temp/{source}/{name}.tar.gz")
    params:
        file = "{name}.tar.gz"
    run:
        link = find_corresponding_link(wildcards, params)
        shell(f"wget -O {output} {link}")


rule unarchive_individual_problem:
    input:
        "resources/problem_archives/{name}.tar.gz/"
    params:
        file = "{name}.tar.gz"
    output:
        "resources/problems/{name}"
    shell:
        "tar -xf {file} -C {output}"


checkpoint unarchive_all_problems:
    input:
        unpack(lambda wildcards: checkpoints.download_all_problems.get(**wildcards).output[0])
    output:
        directory("resources/problems")
    shell:
        ""


checkpoint download_all_problems:
    input:
        *get_resource_names("satlib"),
        *get_resource_names("miplib"),
    output:
        directory("resources/problem_archives")
    run:
        shell("mkdir -p {output}")
        for file in input:
            final_name = os.path.basename(file)
            shell("mv {file} {output}/{final_name}")
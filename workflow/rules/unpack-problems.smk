include: "download-problems.smk"


rule unpack_tar:
    input:
        "resources/problem_archives/{source}/{filename}.tar.gz",
    output:
        temp(directory("temp/problems/{source}/{filename}")),
    shell:
        "mkdir -p {output} && tar -xf {input} -C {output} --warning=none"


rule unpack_zip:
    input:
        "resources/problem_archives/{source}/{filename}.zip",
    output:
        temp(directory("temp/problems/{source}/{filename}")),
    shell:
        "mkdir -p {output} && unzip {input} -d {output}"


def aggregate_archive_files(wildcards):
    checkpoint_output = checkpoints.download_all_problems.get(**wildcards).output[0]
    sources = glob_wildcards(os.path.join(checkpoint_output, "{source,\w+\/.+}")).source
    sources = [
        source.removesuffix(".zip").removesuffix(".tar.gz") for source in sources
    ]
    return expand("temp/problems/{source}", source=sources)


checkpoint unpack_all_problems:
    input:
        aggregate_archive_files,
    output:
        directory("resources/problems"),
    run:
        shell("mkdir -p {output}")
        for archive_output_dir in input:
            inner_output_dir = archive_output_dir
            final_name = os.path.basename(inner_output_dir)
            shell(f"cp -r {inner_output_dir} {output}/{final_name}")

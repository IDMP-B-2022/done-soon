from pathlib import Path


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


def list_archive_output_directories(wildcards):
    download_output_path = Path(
        checkpoints.download_all_problems.get(**wildcards).output[0]
    )

    # download_output_path.glob("**/*.tar.gz")
    sources = glob_wildcards(download_output_path / "{source,\w+\/.+}").source
    sources = [
        source.removesuffix(".zip").removesuffix(".tar.gz") for source in sources
    ]
    print(sources)
    return expand("temp/problems/{source}", source=sources)


checkpoint unpack_all_problems:
    input:
        list_archive_output_directories,
    output:
        directory("resources/problems"),
    run:
        shell("mkdir -p {output}")
        for archive_output_dir in input:
            inner_output_dir = archive_output_dir
            final_name = os.path.basename(inner_output_dir)
            shell(f"cp -r {inner_output_dir} {output}/{final_name}")

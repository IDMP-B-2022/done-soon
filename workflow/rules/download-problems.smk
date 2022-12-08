import argparse
import json
import os

from pathlib import Path

from bs4 import BeautifulSoup
import requests


def get_archive_links(source: str) -> list[str]:
    list_of_links = []
    match source:
        case "satlib":
            base_url = "https://www.cs.ubc.ca/~hoos/SATLIB/"
            res = requests.get(base_url + "benchm.html", timeout=5)
            soup = BeautifulSoup(res.text, "html.parser")

            list_of_links = [
                base_url[8:] + link.get("href")
                for link in soup.find_all("a")
                if link.get("href")[-7:] == ".tar.gz"
            ]
        case "miplib":
            list_of_links = [
                "drive.google.com/uc?id=1n0RZLUdFBW4Nhmdwj02VqW_gG6s8S8I8&confirm=t"
            ]
        case "minizinc_benchmark":
            list_of_links = [
                "github.com/MiniZinc/minizinc-benchmarks/archive/refs/heads/master.zip"
            ]
        case "minizinc_challenges":
            list_of_links = [
                f"www.minizinc.org/challenge{year}/mznc{year}-probs.tar.gz"
                for year in range(2013, 2021)
            ] + [
                f"www.minizinc.org/challenge{year}/mznc{year}_probs.tar.gz"
                for year in range(2021, 2023)
            ]
    return list_of_links


def find_corresponding_link(wildcards, problem_sources):
    for source in problem_sources:
        links = get_archive_links(source)
        for link in links:
            if wildcards.file in link:
                return link


def get_archive_paths(
    problem_sources: list[Path],
):
    """
    Take the "problem_sources" array from the config file
    and get all corresponding paths to archives for the sources.
    These paths are where the files will be stored.
    """
    paths = []
    for source in problem_sources:
        base_path = Path(f"temp/problem_archives/{source}")
        if source == "miplib":
            paths += [base_path / "miplib.zip"]
        else:
            remote_links = get_archive_links(source)
            paths += [base_path / os.path.basename(link) for link in remote_links]
    return paths

rule download_miplib_archive:
    output:
        temp("temp/problem_archives/miplib/miplib.zip"),
    params:
        link="1n0RZLUdFBW4Nhmdwj02VqW_gG6s8S8I8",
    conda:
        "../envs/download-problems.yaml"
    shell:
        "gdown -O {output} {params.link}"


rule download_archive:
    output:
        temp("temp/problem_archives/{source}/{file}"),
    run:
        link = find_corresponding_link(wildcards, config["problem_sources"])
        shell(f"wget -O {output} {link}")


checkpoint download_all_problems:
    input:
        *get_archive_paths(config["problem_sources"]),
    output:
        directory("resources/problem_archives"),
    run:
        path_to_temp = Path(input[0]).parent
        print("input:", input)
        for file in get_archive_paths(config["problem_sources"]):
            final_name = Path(str(output), file.parent.name, file.name)
            final_name.parent.mkdir(parents=True, exist_ok=True)
            shell("cp {file} {final_name}")

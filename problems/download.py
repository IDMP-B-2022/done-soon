import argparse
import glob
import os
import shutil
import tarfile
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

import gdown
from rich import print
from rich.progress import track

# problem sources
CHALLENGE_LIST = [
    f"https://www.minizinc.org/challenge{year}/mznc{year}-probs.tar.gz"
    for year in range(2013, 2021)
] + [
    f"https://www.minizinc.org/challenge{year}/mznc{year}_probs.tar.gz"
    for year in range(2021, 2023)
]
MINIZINC_BENCHMARK = 'https://github.com/MiniZinc/minizinc-benchmarks/archive/refs/heads/master.zip'
MIPLIB_CURATED = 'https://drive.google.com/uc?id=1n0RZLUdFBW4Nhmdwj02VqW_gG6s8S8I8&confirm=t'


def download_extract(url, archive_type, location):
    print(f"Downloading {url}")
    res = urlopen(url)
    bytes_read = BytesIO(res.read())
    print("Extracting...")
    match archive_type:
        case "tar":
            file = tarfile.open(fileobj=bytes_read)
            file.extractall(location)
        case "zip":
            file = ZipFile(bytes_read)
            file.extractall(location)
        case _:
            raise ValueError(
                f"archive_type expected 'tar' or 'zip', got {archive_type}.")
    print("Extracted...")


def download_archives_and_extract(problems_dir: Path):
    for challenge_url in track(CHALLENGE_LIST, description="Challenges"):
        download_extract(challenge_url, "tar", problems_dir)

    print("Minizinc Benchmarks")
    download_extract(MINIZINC_BENCHMARK, "zip", problems_dir)

    print("Downloading MIPLIB Problems")
    miplib_filename = problems_dir / "../miplib.zip"
    gdown.download(MIPLIB_CURATED, str(miplib_filename))

    print("Extracting MIPLIB Problems")
    with open(miplib_filename, "rb") as miplib_file:
        file = ZipFile(BytesIO(miplib_file.read()))
        file.extractall(problems_dir / "miplib")
    print("Extracted MIPLIB Problems")

    os.remove(miplib_filename)


def move_all_problems(problems_dir: Path):
    # Put everything into one directory (out of their individual
    # archive directories)
    for archive in problems_dir.iterdir():
        if archive.is_dir() and archive.name != "miplib":
            shutil.copytree(archive, problems_dir, dirs_exist_ok=True)
            shutil.rmtree(archive)


def move_dzn_to_data_dirs(problems_dir: Path):
    for indiv_prob_path in problems_dir.iterdir():
        if indiv_prob_path.is_file():
            continue

        data_dir: Path = indiv_prob_path / "data"
        data_dir.mkdir(exist_ok=True)

        for dzn in glob.glob(os.path.join(indiv_prob_path, "**/*.dzn")):
            os.rename(dzn, os.path.join(data_dir, os.path.basename(dzn)))

        for dzn in glob.glob(os.path.join(indiv_prob_path, "*.dzn")):
            os.rename(dzn, os.path.join(data_dir, os.path.basename(dzn)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--destination", required=True, type=Path)
    args = parser.parse_args()

    problems_dir: Path = args.destination

    download_archives_and_extract(problems_dir)

    move_all_problems(problems_dir)

    move_dzn_to_data_dirs(problems_dir)

    os.remove(problems_dir / "LICENSE")
    os.remove(problems_dir / "README")
    os.remove(problems_dir / "README.md")


if __name__ == "__main__":
    main()

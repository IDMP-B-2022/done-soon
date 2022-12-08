import argparse
import json
from pathlib import Path

from bs4 import BeautifulSoup
import requests


def get_archive_links(source: str) -> list[str]:
    list_of_links = []
    match source:
        case "satlib":
            base_url = 'https://www.cs.ubc.ca/~hoos/SATLIB/'
            res = requests.get(base_url + '/benchm.html', timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')

            list_of_links = [
                base_url[8:] + link.get('href')
                for link in soup.find_all('a')
                if link.get('href')[-7:] == '.tar.gz'
            ]
        case "miplib":
            list_of_links = [
                'drive.google.com/uc?id=1n0RZLUdFBW4Nhmdwj02VqW_gG6s8S8I8&confirm=t']
        case "minizinc_benchmark":
            list_of_links = [
                'github.com/MiniZinc/minizinc-benchmarks/archive/refs/heads/master.zip']
        case "minizinc_challenges":
            list_of_links = [
                f"www.minizinc.org/challenge{year}/mznc{year}-probs.tar.gz"
                for year in range(2013, 2021)
            ] + [
                f"www.minizinc.org/challenge{year}/mznc{year}_probs.tar.gz"
                for year in range(2021, 2023)
            ]
    return list_of_links


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o", "--output", help="Output directory", type=Path, required=True)
    args = parser.parse_args()

    for source in ["miplib", "satlib", "minizinc_challenges", "minizinc_benchmark"]:
        list_of_links = get_archive_links(source)
        if not args.output.exists():
            args.output.mkdir()

        with open(f"{args.output}/links-{source}.json", "w") as out_file:
            json.dump(list_of_links, out_file, indent=4)


if __name__ == "__main__":
    main()

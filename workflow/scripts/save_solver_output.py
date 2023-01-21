"""
Writes every Nth line to the file passed as
a command line argument.
"""
import argparse
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("outfile_path", type=Path)
parser.add_argument("--N", type=int,
    help="Write every N lines", default=100)
args = parser.parse_args()

N = args.N

outfile_path = Path(args.outfile_path)
outfile_path.parent.mkdir(exist_ok=True, parents=True)

with open(outfile_path, 'w', encoding='utf-8') as outfile:
    for i, line in enumerate(sys.stdin):
        if i % N == 0:
            outfile.write(line)

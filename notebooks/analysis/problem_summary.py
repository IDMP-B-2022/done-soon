import argparse
import glob
from rich.progress import track

from pathlib import Path

import pandas as pd

import enum

from rich.console import Console
from rich.markdown import Markdown

class ProblemType(enum.Enum):
    UNKNOWN = 0
    SAT = 1
    OPT = 2


def main(args):
    console = Console()
    data_dir = Path(args.data_dir)

    if not data_dir.exists() and data_dir.is_dir():
        raise ValueError(f"Data directory {data_dir} does not exist")
    
    fzn_files = list(glob.glob(f"{data_dir}/*.fzn"))
    summary = []

    console.log(f"Found {len(fzn_files)} fzn files")

    for fzn_file in track(fzn_files, description="Counting SAT/OPT"):
        with open(fzn_file, "r") as f:
            contents = f.read()
            problem_type = None
            if "satisfy" in contents:
                problem_type = ProblemType.SAT
            elif "minimize" in contents or "maximize" in contents:
                problem_type = ProblemType.OPT
            else:
                problem_type = ProblemType.UNKNOWN
            
            summary.append({
                "Problem": fzn_file,
                "Problem Type": problem_type
            })

    df = pd.DataFrame(summary, dtype=str)

    summary_table = (df
        .groupby("Problem Type")
        .count()
        .reset_index()
        .rename(columns={"Problem": "Count"})
        .replace({"ProblemType.OPT": "Optimization", "ProblemType.SAT": "Satisfiability"})
        .set_index("Problem Type")
    )

    console.print(Markdown(summary_table.to_markdown()))

    with open(args.latex_output_file, "w") as f:
        f.write(summary_table.to_latex())
        console.log(f"Wrote summary table to {args.latex_output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="problems_compiled")
    parser.add_argument("--latex-output-file", type=str, default="problem_summary_table.tex")
    args = parser.parse_args()
    main(args)
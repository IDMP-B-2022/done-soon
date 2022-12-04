import argparse
from pathlib import Path
from rich.progress import track


def convert(file):
    file_type = None
    variables = -1
    clauses = -1

    lines = []
    current_clause = 'constraint '

    with open(file, 'r', encoding='utf8') as cnf_file:
        for line in cnf_file:
            if line[0] == 'p':
                file_type, variables, clauses = line.strip().split()[1:]
                variables = int(variables)
                clauses = int(clauses)
                assert file_type == 'cnf' and variables > 0 and clauses > 0
                array_def = f'array[1..{variables}] of var bool: b;'
                lines.append(array_def)
            elif line[0] == 'c' or line[0] == '%':
                pass  # skip comments
            else:
                for var in line.strip().split():
                    var = int(var)
                    if var == 0:
                        if current_clause != 'constraint ':
                            current_clause += ';'
                            lines.append(current_clause)
                            current_clause = 'constraint '
                    elif var < 0:   # ! var
                        var = abs(var)
                        if current_clause == 'constraint ':
                            current_clause += f'b[{var}] = false'
                        else:
                            current_clause += f' \/ b[{var}] = false'
                    else:           # var
                        if current_clause == 'constraint ':
                            current_clause += f'b[{var}] = true'
                        else:
                            current_clause += f' \/ b[{var}] = true'
    lines.append('solve satisfy;')

    return lines


def process_files(input_path: Path, output_path: Path):
    for file in track(input_path.glob('./**/*.cnf')):
        converted_problem = convert(file)

        with open(output_path / f"{file.stem}.mzn", 'w', encoding='utf8') as minizinc_file:
            minizinc_file.writelines('\n'.join(converted_problem))


def main():
    parser = argparse.ArgumentParser("")
    parser.add_argument("-c", "--cnf", required=True, type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    args = parser.parse_args()

    process_files(args.cnf, args.output)


if __name__ == "__main__":
    main()

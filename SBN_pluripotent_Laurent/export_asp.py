import subprocess
import csv
import re
from functools import reduce
import sys


LP_FILES = [
    "SBN_construction.lp"
]

PREDICATES = ["transition_function"]

MAX_ANSWER_N = 0

def parse_line(line,names,csp=False):
    """Parse a line of asp predicates named name"""
    # Only works for fixed arity for now (two in this case).
    row = {}
    tokens = line.split()
    for token in tokens:
        if csp :
            match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\(([0-9]*)\,([0-9]*)\)?=(-?\d+)', token)
            if match.group(1) in names:
                arg = match.group(2),match.group(3)
                value = match.group(4)
                row[match.group(1) + f"_{arg[0]},{arg[1]}"] = value
        else:
            match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\(([0-9]*)\,([0-9]*)\)', token)
            if match.group(1) in names:
                arg = match.group(2)
                value = match.group(3)
                row[match.group(1) + f"f_{arg}"] = value
    return row


def solve_and_export(lp_files, names, project=[], time_limit = [],parallel = [], constant = [], max_answer_n = 0,output_csv="output.csv"):
    result = subprocess.run(
        ["clingcon", f"{max_answer_n}"] + project + parallel + time_limit + constant + lp_files,
        capture_output=True, text=True
    )


    all_rows = []
    answer_number = 0
    result_iterator = iter(result.stdout.splitlines())


    while (line := next(result_iterator, None)) is not None and not line.startswith(("SATISFIABLE","UNSATISFIABLE","UNKNOWN")):
        line = line.strip()
        print(line)
        if line.startswith("Answer:"):
            answer_number += 1
            line = next(result_iterator, None)
            if line is not None :    
                asp_row = parse_line(line,names)             
            line = next(result_iterator, None)
            line = next(result_iterator, None)
            if line is not None:
                csp_row = parse_line(line,names,csp=True)
                row = asp_row | csp_row
                all_rows.append(row)



    if not all_rows:
        print(f"NO ANSWER FOUND FOR ")
        return



    with open(output_csv, "w", newline="") as f:
        f.truncate(0)
        writer = csv.DictWriter(f, fieldnames=all_rows[0].keys(), restval="")
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Finished successfully ({answer_number} rows written in {output_csv})")



def rec_decomp_base2_vector_sum(d,s):
    """Return the list of d dimensional vector (as list of length d) which sum in base 2 equals s)"""
    if d == 1 :
        return [[s]]
    else :
        return reduce(lambda l1,l2:l1+l2,([v + [i] for v in rec_decomp_base2_vector_sum(d-1,(s-i) // 2)] for i in range(s+1) if (s-i) % 2 == 0))


if __name__ == "__main__":
    solve_and_export(LP_FILES, PREDICATES, max_answer_n = MAX_ANSWER_N, project = ["--project"], output_csv=f"transition_function_output.csv")

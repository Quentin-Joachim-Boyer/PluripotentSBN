import subprocess
import csv
import re
import numpy as np
import itertools
from functools import reduce
import sys


LP_FILES = [
    "decomp-pluripotent-14-05-2023.lp",
    "Fonctions-bool-Cont-cloture-11-12-2023.lp",
    "SBF-cpath-constraints-12-06-2024.lp",
    "setup_decomp.lp",
]

N = int(sys.argv[2])

MAX_DIMENSION = int(sys.argv[1])

# PREDICATES = ["weight","funct"]

def parse_func(line):
    """Parse a line of predicates 'func' """
    func_row = {}
    tokens = line.split()
    for token in tokens:
        asp_match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\(([0-9]*)\,([0-9]*)\)', token)

        name = asp_match.group(1)
        arg = asp_match.group(2)
        value = asp_match.group(3)
        func_row[f"f_{arg}"] = value
    return func_row

def parse_weight(line):
    """Parse a line of CP predicates 'weight' """
    weight_row = {}
    tokens = line.split()

    for token in tokens:
        csp_match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\(([0-9]*)\,([0-9]*)\)?=(-?\d+)', token)

        name = csp_match.group(1)
        arg = csp_match.group(2),csp_match.group(3)
        value = csp_match.group(4)
        weight_row[f"w_{arg[0]},{arg[1]}"] = value
  
    return weight_row

def solve_and_export(lp_files, decomp_vector, max_answer_n = 0,output_csv="output.csv"):
    d = len(decomp_vector)
    constant = [f"-c v{d-1-i}={decomp_vector[i]}" for i in range(d)]
    parallel = ["--parallel","2"]
    time_limit = ["--time-limit=3600"]
    result = subprocess.run(
        ["clingcon", f"{max_answer_n}","--project",f"-c d={d}"] + parallel + time_limit + constant + lp_files,
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
                func_row = parse_func(line)             
            line = next(result_iterator, None)
            line = next(result_iterator, None)
            if line is not None:
                weight_row = parse_weight(line)
                row = func_row | weight_row
                all_rows.append(row)



    if not all_rows:
        print(f"NO ANSWER FOUND FOR {d}d <0,"+",".join(map(str, decomp_vector))+">.")
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
    for d in range(MAX_DIMENSION,MAX_DIMENSION+1):
        complete_decomp_vects = rec_decomp_base2_vector_sum(d,2**d)
        print(complete_decomp_vects)
        # print(complete_decomp_vects)
        v_full = [1]+[0 for _ in range(d-1)]
        v_full_name = ",".join(map(str, v_full))
        solve_and_export(LP_FILES, v_full,N, output_csv=f"{d}d_<" + v_full_name + ">_output.csv")
        for v in complete_decomp_vects:
            # print(v)
            v_name = ",".join(map(str, v))
            solve_and_export(LP_FILES, v,N, output_csv=f"{d}d_<0," + v_name + ">_output.csv")

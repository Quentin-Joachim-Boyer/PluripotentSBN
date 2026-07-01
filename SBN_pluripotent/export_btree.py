#!/usr/bin/env python3
"""
export_btree.py — Runs btree_constructor.lp with clingcon and exports
                  results to CSV files compatible with sbn_viz.html.

Replaces export_decomposition.py for use with btree_constructor.lp +
setup_btree_Nd.lp instead of the older decomp-pluripotent-*.lp files.

Usage:
    python3 export_btree.py <max_dim> <n_solutions> [options]

Arguments:
    max_dim       Dimension to enumerate (e.g. 4)
    n_solutions   Max solutions per vector (0 = all)

Options:
    --lp FILE     SBN_pluripotent_undercontrol.lp path (default: SBN_pluripotent_undercontrol.lp)
    --setup DIR   Directory containing setup_btree_Nd.lp files (default: .)
    --out DIR     Output directory for CSV files (default: .)
    --parallel P  clingcon parallel threads (default: 2)
    --time T      clingcon time limit in seconds (default: 3600)
    --vec V       Run only for this vector (e.g. "0,1,2,0,0"), can repeat

Example:
    # Generate all 3d decompositions, 1000 solutions each:
    python3 export_btree.py 3 1000

    # Generate only the <0,2,0,0> and <0,1,2,0,0> cases:
    python3 export_btree.py 4 500 --vec 0,2,0,0 --vec 0,1,2,0,0

Output filenames use double-underscore format compatible with sbn_viz.html:
    e.g.  4d__0_1_2_0_0__output.csv  (no angle brackets, Windows-safe)
"""

import subprocess
import csv
import re
import sys
import argparse
import os
from itertools import product as iproduct


# ─── Vector enumeration ──────────────────────────────────────────────────────

def valid_vecs(n):
    """All valid decomposition vectors for dimension n."""
    seen = set()
    target = 2 ** n
    max_counts = [target // (2 ** (n - i)) for i in range(n + 1)]
    for counts in iproduct(*[range(mc + 1) for mc in max_counts]):
        total = sum(counts[i] * (2 ** (n - i)) for i in range(n + 1))
        if total == target:
            key = tuple(counts)
            if key not in seen:
                seen.add(key)
                yield list(counts)


# ─── Parsing ─────────────────────────────────────────────────────────────────

def parse_transition_bits(line):
    """Parse transition_function_bit(N, S) atoms -> {node: set of active states}"""
    bits = {}
    for m in re.finditer(r'transition_function_bit\((\d+),(\d+)\)', line):
        node, state = int(m.group(1)), int(m.group(2))
        bits.setdefault(node, set()).add(state)
    return bits


def bits_to_str(active_states, n):
    """Truth-table bitstring : caractere s = etat s actif, etat 0 a gauche,
    longueur 2**n. Convention attendue par sbn_viz/transitionsFromF (et
    SBN.toCsvRow du pipeline Java) ; NE PAS confondre avec l'entier decimal."""
    return "".join("1" if s in active_states else "0" for s in range(1 << n))


def parse_weights(line):
    """Parse w(I,J,nil)=V atoms -> {(i,j): value}  (root context only)"""
    return {(int(m.group(1)), int(m.group(2))): int(m.group(3))
            for m in re.finditer(r'w\((\d+),(\d+)\)=(-?\d+)', line)}


# ─── Solver ───────────────────────────────────────────────────────────────────

def run_clingcon(lp_files, constants, n_solutions, time_limit, parallel):
    """Run clingcon and return stdout."""
    const_args = [f"-c {k}={v}" for k, v in constants.items()]
    const_flat = []
    for c in const_args:
        const_flat.extend(c.split())

    cmd = (["clingcon", str(n_solutions), "--project"]
           + const_flat + lp_files)
    
    if parallel is not None:
        cmd += ["--parallel", str(parallel)]

    if time_limit is not None:
        cmd += [f"--time-limit={time_limit}"]


    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode not in (10, 20, 30):
        print(f"  clingcon error (code {result.returncode})", file=sys.stderr)
        if result.stderr:
            print(f"  {result.stderr[:300]}", file=sys.stderr)
    return result.stdout


def parse_output(output, n):
    """Parse clingcon output, return list of {funcs, weights} dicts."""
    solutions = []
    lines = iter(output.splitlines())
    for line in lines:
        line = line.strip()
        if line.startswith("Answer:"):
            atoms_line = next(lines, "").strip()
            bits    = parse_transition_bits(atoms_line)
            funcs   = {node: bits_to_str(active, n) for node, active in bits.items()}

            next(lines, "")
            assignement_line = next(lines, "").strip()
            weights = parse_weights(assignement_line)

            solutions.append({'funcs': funcs, 'weights': weights})
    return solutions


# ─── CSV writer ───────────────────────────────────────────────────────────────

def write_csv(solutions, n, output_path):
    """Write solutions to CSV compatible with sbn_viz.html."""
    f_cols = [f"f_{j}"    for j in range(1, n + 1)]
    w_cols = [f"w_{i},{j}" for i in range(1, n + 1) for j in range(1, n + 1)]

    written = skipped = 0
    rows = []
    for sol in solutions:
        fvals = [sol['funcs'].get(j, "0" * (1 << n)) for j in range(1, n + 1)]
        wvals = [sol['weights'].get((i, j), 0)
                    for i in range(1, n + 1) for j in range(1, n + 1)]
        
        if len(fvals) == n and len(wvals) == n * n:
            rows.append(fvals + wvals)
            written += 1
        else:
            skipped += 1

    rows.sort()
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(f_cols + w_cols)
        for row in rows:
            writer.writerow(row)

    if skipped:
        print(f"  Warning: {skipped} incomplete solutions skipped", file=sys.stderr)
    return written


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("max_dim",      type=int,
                        help="SBN dimension to enumerate")
    parser.add_argument("n_solutions",  type=int,
                        help="Max solutions per vector (0 = all)")
    parser.add_argument("--lp",         default="PSBN_undercontrol.lp",
                        help="Path to the SBN constructor file")
    parser.add_argument("--setup",      default=".",
                        help="Directory containing setup_btree_Nd.lp files")
    parser.add_argument("--out",        default=".",
                        help="Output directory for CSV files")
    parser.add_argument("--parallel",   type=int, default=None)
    parser.add_argument("--time",       type=int, default=None)
    parser.add_argument("--vec",        action="append", default=[],
                        help="Run only for this vector (repeatable)")
    args = parser.parse_args()

    n = args.max_dim
    setup_file = os.path.join(args.setup, f"setup_btree_{n}d.lp")
    if not os.path.exists(setup_file):
        print(f"Error: {setup_file} not found. Run gen_setup_btree.py {n} first.",
              file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.out, exist_ok=True)

    # Determine which vectors to run
    if args.vec:
        vecs = [list(map(int, v.split(","))) for v in args.vec]
    else:
        vecs = list(valid_vecs(n))

    print(f"d={n}: {len(vecs)} vectors to enumerate, {args.n_solutions} solutions each")

    for vec in vecs:
        vec_str = ",".join(map(str, vec))
        vec_tag = "_".join(map(str, vec))
        lp_name = args.lp.removesuffix(".lp")
        csv_name = f"{n}d__{vec_tag}__{lp_name}__output.csv"
        csv_path = os.path.join(args.out, csv_name)

        # Build constants dict: d=n, v0=vec[0], v1=vec[1], ...
        constants = {"d": n}
        for i, val in enumerate(vec):
            vi_name = f"v{n - i}"  # v0 = highest dim count (vec[n])
            constants[vi_name] = val


        print(f"  vec=<{vec_str}> ... ", end="", flush=True)
        output = run_clingcon(
            [setup_file, args.lp],
            constants,
            args.n_solutions,
            args.time,
            args.parallel
        )
        solutions = parse_output(output, n)
        if not solutions:
            print("no solutions found")
            continue
        written = write_csv(solutions, n, csv_path)
        print(f"{written} solutions -> {csv_name}")


if __name__ == "__main__":
    main()
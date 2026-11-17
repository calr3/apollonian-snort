"""
Python front end for the C++ evaluator in csrc/snort.cpp.

The binary computes canonical forms; the resulting game DAG is imported into a
cgt.Games universe, where every imported node is re-canonicalised (so an
error in the C++ code that produced a non-canonical form would be caught by
the reference implementation) unless trust=True.
"""

from __future__ import annotations

import os
import subprocess
from fractions import Fraction

from cgt import Games
from snort import Graph

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, "csrc", "snortc")


def build():
    src = os.path.join(HERE, "csrc", "snort.cpp")
    if not os.path.exists(BIN) or os.path.getmtime(BIN) < os.path.getmtime(src):
        subprocess.check_call(["g++", "-O2", "-std=c++17", "-DLE_CACHE_LOG=22", "-o", BIN, src])


def evaluate(graph: Graph, positions, games: Games, autos=None, trust=False, log=None):
    """Canonical values (ids in `games`) of the given positions [(alive, L, R)]."""
    build()
    if autos is None:
        autos = graph.automorphisms()
    lines = [f"{graph.n} {len(graph.edges)}"]
    lines += [f"{u} {v}" for u, v in graph.edges]
    lines.append(str(len(autos)))
    lines += [" ".join(map(str, p)) for p in autos]
    lines.append(str(len(positions)))
    lines += [f"{a} {l} {r}" for a, l, r in positions]
    proc = subprocess.run([BIN], input="\n".join(lines) + "\n", capture_output=True, text=True, check=True)
    if log is not None:
        log.write(proc.stderr)
    return import_dag(proc.stdout, games, trust)


def import_dag(text: str, games: Games, trust=False):
    it = iter(text.splitlines())
    roots = [int(x) for x in next(it).split()[1:]]
    m = {}
    for line in it:
        p = line.split()
        if p[0] == "N":
            m[int(p[1])] = games.number(Fraction(int(p[2]), 2 ** int(p[3])))
        else:
            gid = int(p[1])
            nl = int(p[2])
            Ls = [m[int(x)] for x in p[3:3 + nl]]
            nr = int(p[3 + nl])
            Rs = [m[int(x)] for x in p[4 + nl:4 + nl + nr]]
            if trust:
                m[gid] = games._intern(tuple(sorted(Ls)), tuple(sorted(Rs)))
            else:
                g = games.canon(Ls, Rs)
                if games.Lo[g] != tuple(sorted(Ls)) or games.Ro[g] != tuple(sorted(Rs)):
                    raise AssertionError(f"C++ produced a non-canonical form for node {gid}")
                m[gid] = g
    return [m[r] for r in roots]

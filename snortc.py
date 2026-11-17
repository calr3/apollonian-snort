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
SRC = os.path.join(HERE, "csrc", "snort.cpp")
# small build: 32 MB comparison cache (tests, small graphs);
# big build: 1 GB cache and native optimisation (depth-4 sized jobs)
BUILDS = {
    False: (os.path.join(HERE, "csrc", "snortc"), ["-O2", "-DLE_CACHE_LOG=22"]),
    True: (os.path.join(HERE, "csrc", "snortc_big"), ["-O3", "-march=native", "-DLE_CACHE_LOG=27"]),
}


def build(big=False):
    path, flags = BUILDS[big]
    if not os.path.exists(path) or os.path.getmtime(path) < os.path.getmtime(SRC):
        subprocess.check_call(["g++", "-std=c++17", *flags, "-o", path, SRC])
    return path


def evaluate(graph: Graph, positions, games: Games, autos=None, trust=False, log=None, big=False,
             progress=False):
    """Canonical values (ids in `games`) of the given positions [(alive, L, R)].

    The binary's progress messages are passed to stderr if `progress`, written to the
    file object `log` if given, and discarded otherwise.
    """
    BIN = build(big)
    if autos is None:
        autos = graph.automorphisms()
    lines = [f"{graph.n} {len(graph.edges)}"]
    lines += [f"{u} {v}" for u, v in graph.edges]
    lines.append(str(len(autos)))
    lines += [" ".join(map(str, p)) for p in autos]
    lines.append(str(len(positions)))
    lines += [f"{a} {l} {r}" for a, l, r in positions]
    proc = subprocess.run([BIN], input="\n".join(lines) + "\n", stdout=subprocess.PIPE,
                          stderr=None if progress else subprocess.PIPE, text=True, check=True)
    if log is not None and not progress:
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

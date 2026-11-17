"""
Compute Snort on deterministic Apollonian networks of increasing depth and
print a summary (Markdown table + Left's first-move values by vertex class).

usage:  python3 explore.py [max_depth] [--both-faces] [--python]

The C++ back end (csrc/snort.cpp, built automatically) is used by default;
--python uses the pure-Python reference implementation instead (fine up to
depth 3).  Depth 4 is beyond exhaustive evaluation (a single first move needs
over 10^8 components); see depth4.py for how its value is determined.
"""

from __future__ import annotations

import json
import sys
import time
from fractions import Fraction

from apollonian import apollonian
from cgt import Games
from snort import Snort
import snortc


def fmt(q: Fraction) -> str:
    return str(q.numerator) if q.denominator == 1 else f"{q.numerator}/{q.denominator}"


def analyse(depth: int, games: Games, both_faces=False, use_python=False):
    graph, info = apollonian(depth, outer_face=both_faces)
    positions = [(graph.full, 0, 0)]
    for v in range(graph.n):
        a = graph.full & ~(1 << v)
        positions.append((a, graph.adj[v] & a, 0))
    t0 = time.time()
    if use_python:
        s = Snort(graph, games)
        vals = [s.value(*p) for p in positions]
    else:
        vals = snortc.evaluate(graph, positions, games, trust=depth >= 4, big=graph.n > 30,
                               progress=graph.n > 30)
    elapsed = time.time() - t0
    v = vals[0]
    th = games.thermograph(v)
    Ls, Rs = games.stops(v)
    moves = []
    for vtx in range(graph.n):
        val = vals[1 + vtx]
        moves.append({
            "vertex": vtx,
            "level": info["level"][vtx],
            "degree": graph.degree(vtx),
            "value": games.show(val),
            "mean": fmt(games.mean(val)),
            "temperature": fmt(games.temperature(val)),
            "dominated_by_centre": depth >= 1 and games.le(val, vals[1 + 3]),
        })
    return {
        "depth": depth,
        "vertices": graph.n,
        "edges": len(graph.edges),
        "max_degree": max(graph.degree(x) for x in range(graph.n)),
        "value": games.show(v),
        "temperature": fmt(th.temperature),
        "mean": fmt(th.mean),
        "left_stop": fmt(Ls),
        "right_stop": fmt(Rs),
        "outcome": games.outcome(v),
        "canonical_subpositions": games.size(v),
        "birthday": games.birthday(v),
        "left_moves_in_canonical_form": len(games.Lo[v]),
        "seconds": round(elapsed, 2),
        "left_moves": moves,
    }


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    both = "--both-faces" in sys.argv
    use_python = "--python" in sys.argv
    max_depth = int(args[0]) if args else 3
    games = Games()
    rows = []
    for d in range(max_depth + 1):
        r = analyse(d, games, both, use_python)
        rows.append(r)
        print(f"depth {d}: |V|={r['vertices']} value={r['value']} t={r['temperature']} ({r['seconds']}s)",
              flush=True)
        seen = set()
        for m in r["left_moves"]:
            key = (m["level"], m["degree"], m["value"])
            if key in seen:
                continue
            seen.add(key)
            dom = " (<= centre move)" if m["dominated_by_centre"] else ""
            print(f"    Left colours a level-{m['level']} vertex (deg {m['degree']}): "
                  f"{m['value']}   [mean {m['mean']}, temp {m['temperature']}]{dom}")
        name = "data/results_both_faces.json" if both else "data/results.json"
        with open(name, "w") as f:
            json.dump(rows, f, indent=1)
    print()
    print("| n | vertices | edges | Δ | value | temperature | stops | outcome |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['depth']} | {r['vertices']} | {r['edges']} | {r['max_degree']} | {r['value']} | "
              f"{r['temperature']} | {r['left_stop']}, {r['right_stop']} | {r['outcome']} |")


if __name__ == "__main__":
    main()

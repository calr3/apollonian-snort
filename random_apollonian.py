"""
Snort on random Apollonian networks (random planar 3-trees: start from a
triangle and repeatedly insert a vertex into a uniformly random inner face).

For each sample records the canonical value, temperature, maximum degree and
whether the value is a pure switch {x | -x} with x a number.  Used to test
which features of the deterministic family are special.

usage: python3 random_apollonian.py N_MIN N_MAX SAMPLES SEED > out.jsonl
"""

from __future__ import annotations

import json
import random
import sys

from cgt import Games
from snort import Graph
import snortc


def random_apollonian(n: int, rng: random.Random) -> Graph:
    edges = {(0, 1), (1, 2), (0, 2)}
    faces = [(0, 1, 2)]
    for v in range(3, n):
        a, b, c = faces.pop(rng.randrange(len(faces)))
        edges |= {(a, v), (b, v), (c, v)}
        faces += [(a, b, v), (b, c, v), (a, c, v)]
    return Graph(n, edges)


def main():
    nmin, nmax, samples, seed = map(int, sys.argv[1:5])
    rng = random.Random(seed)
    for n in range(nmin, nmax + 1):
        for _ in range(samples):
            games = Games()
            g = random_apollonian(n, rng)
            pos = [(g.full, 0, 0)]
            for v in range(n):
                na = g.full & ~(1 << v)
                pos.append((na, g.adj[v] & na, 0))
            vals = snortc.evaluate(g, pos, games, trust=True)
            v = vals[0]
            degs = [g.degree(x) for x in range(n)]
            lo = games.Lo[v]
            best = max(range(n), key=lambda x: (games.mean(vals[1 + x]), degs[x]))
            rec = {
                "n": n,
                "edges": g.edges,
                "value": games.show(v),
                "temperature": str(games.temperature(v)),
                "max_degree": max(degs),
                "pure_switch": len(lo) == 1 and games.is_number(lo[0]),
                "best_mean_move_degree": degs[best],
                "left_moves_in_canonical_form": len(lo),
            }
            print(json.dumps(rec), flush=True)


if __name__ == "__main__":
    main()

"""
Partial analysis of Snort on A4 (43 vertices).

The full canonical form of A4 is out of reach: a single first move at a
degree-6 vertex already generates over 10^8 distinct components.  This script
records what *can* be established rigorously:

  * C4, the position after Left colours the centre d, exactly;
  * for every other first move v, the cheap position X_v obtained when Left
    has coloured both v and d; by Lemmas A and B below, P_v <= 1 + X_v, where
    P_v is the position after Left colours v.  If 1 + X_v <= C4 the move at v
    is dominated by the centre move;
  * exact values of the cheaper first moves (corner and level 2) if requested;
  * bounds on the temperature:  mean(C4) <= t(A4) <= max over Left first moves
    P of mean(P), with mean(P_v) <= 1 + mean(X_v) when P_v is not known exactly.

Lemma A (monotonicity).  Adding Left tints to vertices and deleting
Right-tinted vertices never decreases the value.
Lemma B.  If u is Left-tinted in Q, then Q <= 1 + Q', where Q' is Q after
Left colours u.
Both are proved by mirror strategies (see README) and are checked on random
positions in tests/test_engine.py.

usage: python3 depth4.py [--exact]      (--exact adds the corner and level-2
                                          moves; a few minutes, ~3 GB RAM)
"""

from __future__ import annotations

import json
import sys

from apollonian import apollonian
from cgt import Games
import snortc


def fmt(q):
    return str(q.numerator) if q.denominator == 1 else f"{q.numerator}/{q.denominator}"


def main():
    exact = "--exact" in sys.argv
    G = Games()
    g, info = apollonian(4)
    autos = g.automorphisms()
    d = 3
    reps = sorted({min(p[v] for p in autos) for v in range(g.n)})
    orbit = {v: sorted({p[v] for p in autos}) for v in reps}

    def after_left(*vs):
        a = g.full
        L = 0
        for v in vs:
            a &= ~(1 << v)
            L |= g.adj[v]
        return (a, L & a, 0)

    C4 = snortc.evaluate(g, [after_left(d)], G, trust=True, big=True)[0]
    others = [v for v in reps if v != d]
    X = dict(zip(others, snortc.evaluate(g, [after_left(v, d) for v in others], G, trust=True, big=True)))
    P = {}
    if exact:
        for v in (0, 4):  # corner and level-2 moves
            P[v] = snortc.evaluate(g, [after_left(v)], G, trust=True, big=True, progress=True)[0]

    rows = []
    mean_bound = G.mean(C4)
    for v in reps:
        row = {"vertex": v, "orbit_size": len(orbit[v]), "level": info["level"][v],
               "degree": g.degree(v), "adjacent_to_centre": bool(g.adj[d] >> v & 1)}
        if v == d:
            row.update(value=G.show(C4), mean=fmt(G.mean(C4)), temperature=fmt(G.temperature(C4)),
                       status="centre move C4")
        elif v in P:
            dom = G.le(P[v], C4)
            row.update(value=G.show(P[v]), mean=fmt(G.mean(P[v])),
                       temperature=fmt(G.temperature(P[v])),
                       status="exact; dominated by C4" if dom else "exact; NOT dominated by C4")
            mean_bound = max(mean_bound, G.mean(P[v]))
        else:
            b = G.add(G.ONE, X[v])
            dom = G.le(b, C4)
            row.update(X_v=G.show(X[v]), mean_upper_bound=fmt(1 + G.mean(X[v])),
                       status="dominated by C4 (1 + X_v <= C4)" if dom else "unresolved")
            mean_bound = max(mean_bound, 1 + G.mean(X[v]))
        rows.append(row)
        print(row, flush=True)
    summary = {
        "C4": G.show(C4),
        "temperature_lower_bound": fmt(G.mean(C4)),
        "temperature_upper_bound": fmt(mean_bound),
        "left_stop_lower_bound": fmt(G.stops(C4)[1]),
        "first_moves": rows,
    }
    print(summary["temperature_lower_bound"], "<= t(A4) <=", summary["temperature_upper_bound"])
    if exact:
        with open("data/depth4.json", "w") as f:
            json.dump(summary, f, indent=1)


if __name__ == "__main__":
    main()

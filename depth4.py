"""
Snort on A4 (43 vertices), determined without exhaustive search.

Exhaustive evaluation of A4 is out of reach: a single first move at a degree-6
vertex already generates over 10^8 distinct components.  This script instead
shows that every Left first move is <= C4 (the centre move), which gives
A4 = {C4 | -C4}.  It computes:

  * C4, the position after Left colours the centre d, exactly;
  * for every other first move v and every "hub" u among the seven vertices of
    level <= 2, the cheap position X_{v,u} obtained when Left has coloured both
    v and u.  By Lemmas A and B below, P_v <= 1 + X_{v,u}, where P_v is the
    position after Left colours v.  If 1 + X_{v,u} <= C4 for some u, the move at
    v is dominated by the centre move, and in any case
    mean(P_v) <= 1 + min_u mean(X_{v,u});
  * exact values of the cheaper first moves (corner and level 2) if requested;
  * bounds on the temperature:  mean(C4) <= t(A4) <= max over Left first moves
    P of mean(P), using the bound above when P_v is not known exactly.

Lemma A (monotonicity).  Adding Left tints to vertices and deleting
Right-tinted vertices never decreases the value.
Lemma B.  If u is Left-tinted in Q, then Q <= 1 + Q', where Q' is Q after
Left colours u.
Both are proved by mirror strategies (see README) and are checked on random
positions in tests/test_engine.py.

usage: python3 depth4.py --exact        (the corner and level-2 moves are
                                          computed exactly: ~15 min, ~3 GB RAM;
                                          the hub bounds take ~10 min per class)
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
    hubs = list(range(7))  # corners, centre, level-2 vertices
    P = {}
    if exact:
        for v in (0, 4):  # corner and level-2 moves
            P[v] = snortc.evaluate(g, [after_left(v)], G, trust=True, big=True, progress=True)[0]

    def second_criterion(v, best):
        """P_v <= C4 iff no C4^R <= P_v and no P_v^L >= C4.

        C4^R <= P_v is excluded when mean(P_v) < mean(C4^R).  The Left options
        of P_v are the X_{v,w}; for hubs w they are compared with C4 directly,
        otherwise X_{v,w} >= C4 is excluded by mean(X_{v,w}) <= 1 + mean(X_{v,w,u})
        < mean(C4), with u the best hub for v.
        """
        if any(best[0] >= G.mean(r) for r in G.Ro[C4]):
            return False
        u = best[1]
        far = [w for w in range(g.n) if w != v and w not in hubs]
        for w in hubs:
            if w != v:
                x = snortc.evaluate(g, [after_left(v, w)], G, trust=True, big=True)[0]
                if G.le(C4, x):
                    return False
        ys = snortc.evaluate(g, [after_left(v, w, u) for w in far], G, trust=True, big=True)
        return all(1 + G.mean(y) < G.mean(C4) for y in ys)

    rows = []
    mean_bound = G.mean(C4)
    # Left stop of A4 = max over Left options of their Right stop; R(P) <= mean(P)
    stop_bound = G.stops(C4)[1]
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
            stop_bound = max(stop_bound, G.stops(P[v])[1])
        else:
            best, dom_hub = None, None
            for u in hubs:
                if u == v:
                    continue
                x = snortc.evaluate(g, [after_left(v, u)], G, trust=True, big=True)[0]
                b = 1 + G.mean(x)
                if best is None or b < best[0]:
                    best = (b, u)
                if dom_hub is None and G.le(G.add(G.ONE, x), C4):
                    dom_hub = u
            status = (f"dominated by C4 (1 + X_v,u <= C4 with u = {dom_hub})"
                      if dom_hub is not None else "unresolved")
            if dom_hub is None and second_criterion(v, best):
                status = "dominated by C4 (second criterion: no Left option of P_v is >= C4)"
            row.update(mean_upper_bound=fmt(best[0]), best_hub=best[1], status=status)
            mean_bound = max(mean_bound, best[0])
            stop_bound = max(stop_bound, best[0])
        rows.append(row)
        print(row, flush=True)
    all_dominated = all(r["status"].startswith(("dominated", "exact; dominated", "centre"))
                        for r in rows)
    A4 = G.canon([C4], [G.neg(C4)]) if all_dominated else None
    summary = {
        "C4": G.show(C4),
        "A4": G.show(A4) if A4 is not None else None,
        "A4_temperature": fmt(G.temperature(A4)) if A4 is not None else None,
        "A4_stops": [fmt(x) for x in G.stops(A4)] if A4 is not None else None,
        "temperature_lower_bound": fmt(G.mean(C4)),
        "temperature_upper_bound": fmt(mean_bound),
        "left_stop_lower_bound": fmt(G.stops(C4)[1]),
        "left_stop_upper_bound": fmt(stop_bound),
        "first_moves": rows,
    }
    if A4 is not None:
        print("every first move is <= C4, so A4 =", summary["A4"], "temperature", summary["A4_temperature"],
              "stops", summary["A4_stops"])
    print(summary["temperature_lower_bound"], "<= t(A4) <=", summary["temperature_upper_bound"])
    print(summary["left_stop_lower_bound"], "<= Left stop of A4 <=", summary["left_stop_upper_bound"])
    if exact:
        with open("data/depth4.json", "w") as f:
            json.dump(summary, f, indent=1)


if __name__ == "__main__":
    main()

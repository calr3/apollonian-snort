"""
Exhaustive Snort survey of all planar 3-trees (Apollonian networks in the
broad sense: triangulations obtained from a triangle by repeatedly stacking a
vertex into a face) with up to N vertices, up to isomorphism.

Isomorphism classes are found with a canonical code of the planar embedding
(maximal planar graphs on >= 4 vertices are 3-connected, so their embedding is
unique up to reflection): for every directed edge and both orientations a
BFS code is generated and the lexicographically least one is kept.

usage: python3 enumerate_3trees.py N_MAX > data/planar3trees.jsonl
"""

from __future__ import annotations

import json
import sys

from cgt import Games
from snort import Graph
import snortc


class Triangulation:
    def __init__(self, n, rot, faces):
        self.n = n
        self.rot = rot  # rot[v]: neighbours in counter-clockwise order
        self.faces = faces  # all faces, each (a, b, c) counter-clockwise

    @staticmethod
    def triangle():
        return Triangulation(3, [[1, 2], [2, 0], [0, 1]], [(0, 1, 2), (0, 2, 1)])

    def stack(self, fi):
        a, b, c = self.faces[fi]
        v = self.n
        rot = [r[:] for r in self.rot]
        for x, y, z in ((a, b, c), (b, c, a), (c, a, b)):
            r = rot[x]
            i = r.index(y)
            assert r[(i + 1) % len(r)] == z
            r.insert(i + 1, v)
        rot.append([a, b, c])
        faces = self.faces[:fi] + self.faces[fi + 1:] + [(a, b, v), (b, c, v), (c, a, v)]
        return Triangulation(v + 1, rot, faces)

    def edges(self):
        return [(u, w) for u in range(self.n) for w in self.rot[u] if u < w]

    def code(self):
        best = None
        for u in range(self.n):
            for w in self.rot[u]:
                for d in (1, -1):
                    num = {u: 1}
                    ref = {u: w}
                    queue = [u]
                    code = []
                    qi = 0
                    while qi < len(queue):
                        x = queue[qi]
                        qi += 1
                        r = self.rot[x]
                        k = r.index(ref[x])
                        for j in range(len(r)):
                            y = r[(k + d * j) % len(r)]
                            if y not in num:
                                num[y] = len(num) + 1
                                ref[y] = x
                                queue.append(y)
                            code.append(num[y])
                        code.append(0)
                        if best is not None and code > best[:len(code)]:
                            break
                    if best is None or code < best:
                        best = code
        return tuple(best)


def main():
    nmax = int(sys.argv[1])
    level = {Triangulation.triangle().code(): Triangulation.triangle()}
    n = 3
    while True:
        games = Games()
        for t in level.values():
            g = Graph(t.n, t.edges())
            v = snortc.evaluate(g, [(g.full, 0, 0)], games, trust=True)[0]
            degs = [g.degree(x) for x in range(t.n)]
            lo = games.Lo[v]
            print(json.dumps({
                "n": t.n,
                "edges": g.edges,
                "max_degree": max(degs),
                "value": games.show(v),
                "temperature": str(games.temperature(v)),
                "pure_switch": len(lo) == 1 and games.is_number(lo[0]),
            }), flush=True)
        print(f"n={n}: {len(level)} planar 3-trees", file=sys.stderr, flush=True)
        if n == nmax:
            break
        nxt = {}
        for t in level.values():
            for fi in range(len(t.faces)):
                s = t.stack(fi)
                c = s.code()
                if c not in nxt:
                    nxt[c] = s
        level = nxt
        n += 1


if __name__ == "__main__":
    main()

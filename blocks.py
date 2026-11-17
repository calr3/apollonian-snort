"""
Building blocks of Snort on Apollonian networks.

  T_k        : the depth-k network whose three outer corners are tinted for
               Left (uncoloured, but only Left may colour them) and whose
               interior is untinted.  After Left colours the centre of A_n,
               the untinted part of the board is a union of such triangles
               glued along shared corners.
  I_k(x,y,z) : the interior of the depth-k network after its corners have
               been resolved: each corner is coloured by Left (L), by Right
               (R) or is dead/absent (0).  Once all three corners of a
               separating triangle are resolved, its inside is an independent
               summand with exactly this value.

usage: python3 blocks.py K_MAX
"""

from __future__ import annotations

import itertools
import sys

from apollonian import apollonian
from cgt import Games
import snortc


def block_positions(k: int):
    g, _ = apollonian(k)
    interior = g.full & ~0b111
    pos = {}
    pos["T"] = (g.full, 0b111, 0)
    for states in itertools.combinations_with_replacement("0LR", 3):
        L = R = 0
        for corner, s in zip(range(3), states):
            if s == "L":
                L |= g.adj[corner]
            elif s == "R":
                R |= g.adj[corner]
        pos["I(" + ",".join(states) + ")"] = (interior, L & interior, R & interior)
    return g, pos


def main():
    kmax = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    games = Games()
    for k in range(kmax + 1):
        g, pos = block_positions(k)
        names = list(pos)
        vals = snortc.evaluate(g, [pos[x] for x in names], games, trust=True)
        for name, v in zip(names, vals):
            print(f"k={k} {name:10s} {games.show(v):60s} mean {games.mean(v)} temp {games.temperature(v)}",
                  flush=True)


if __name__ == "__main__":
    main()

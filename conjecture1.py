"""
Checks behind Section 9 of the README ("Toward Conjecture 1").

  1. Theorem C1 applied to A_n: every level-n vertex v satisfies N[v] in N[x] for each of
     its three neighbours x, and N[x] is not contained in N[v]; so the move at v is
     strictly dominated.  3*2^(n-2) of them are neighbours of the centre.
  2. The structure of C_n (Left has coloured the centre): the number k of isolated
     Left-tinted vertices, and the pockets (components left after deleting all
     Left-tinted vertices), which must be 3*2^(n-2-j) copies of the open interior of a
     depth-j network for j = 1..n-2.
  3. Theorem C2 (the centre move is winning): C_n >= k + I_{n-2}(0,0,0) >= k - |I_{n-2}|,
     positive for n <= 6; for n = 7 via I_5 <= 1 + 3*I_4(0,0,L) and L(3*I_4(0,0,L)) < k - 1.
  4. Sanity checks with exact values at small depth, and which first moves are winning.

usage: python3 conjecture1.py          (about a minute)
"""

from __future__ import annotations

from collections import Counter

from apollonian import apollonian
from blocks import block_positions
from cgt import Games
from snort import Snort, bits
import snortc

G = Games()


def popcount(m):
    return bin(m).count("1")


def theorem_c1(n):
    g, info = apollonian(n)
    d = 3
    closed = [g.adj[v] | (1 << v) for v in range(g.n)]
    level_n = [v for v in range(g.n) if info["level"][v] == n]
    for v in level_n:
        assert g.degree(v) == 3
        for x in bits(g.adj[v]):
            assert closed[v] & ~closed[x] == 0, (n, v, x)  # N[v] inside N[x]
            assert closed[x] & ~closed[v] != 0, (n, v, x)  # x has a neighbour outside N[v]
    next_to_centre = sum(1 for v in level_n if g.adj[d] >> v & 1)
    assert len(level_n) == 3 ** (n - 1)
    assert next_to_centre == 3 * 2 ** (n - 2)
    return len(level_n), next_to_centre, g.n


def components(g, alive):
    out = []
    rem = alive
    while rem:
        comp = rem & -rem
        frontier = comp
        while frontier:
            new = 0
            for v in bits(frontier):
                new |= g.adj[v] & alive
            new &= ~comp
            comp |= new
            frontier = new
        out.append(comp)
        rem &= ~comp
    return out


def centre_structure(n):
    g, info = apollonian(n)
    d = 3
    alive = g.full & ~(1 << d)
    L = g.adj[d]
    U = alive & ~L
    # isolated Left-tinted vertices: no untinted neighbour (edges between tinted vertices are irrelevant)
    k = sum(1 for v in bits(L) if g.adj[v] & U == 0)
    pockets = components(g, U)
    sizes = Counter(popcount(p) for p in pockets)
    expected = Counter({(3 ** j - 1) // 2: 3 * 2 ** (n - 2 - j) for j in range(1, n - 1)})
    assert sizes == expected, (n, sizes, expected)
    # each pocket has the degree sequence of the open interior of A_j (A_j minus its corners)
    reference = {}
    for j in range(1, n - 1):
        gj, _ = apollonian(j)
        inner = gj.full & ~0b111
        reference[(3 ** j - 1) // 2] = sorted(popcount(gj.adj[v] & inner) for v in bits(inner))
    for p in pockets:
        degs = sorted(popcount(g.adj[v] & p) for v in bits(p))
        assert degs == reference[popcount(p)], (n, popcount(p))
    return k, sizes, popcount(U)


def main():
    print("Theorem C1 on A_n (level-n first moves are strictly dominated by each neighbour):")
    for n in range(2, 8):
        cnt, near, nv = theorem_c1(n)
        print(f"  n={n}: |V|={nv}, level-n vertices {cnt} (strictly dominated), "
              f"{near} of them by the centre itself")

    print("\nStructure of C_n and the bound C_n >= k + I_(n-2)(0,0,0) >= k - (3^(n-2)-1)/2:")
    ks = {}
    for n in range(3, 8):
        k, sizes, nu = centre_structure(n)
        ks[n] = k
        assert k == 3 * 2 ** (n - 2)
        bound = k - (3 ** (n - 2) - 1) // 2
        print(f"  n={n}: k={k} isolated Left-tinted, {nu} untinted in pockets "
              f"{dict(sorted(sizes.items()))} (size: copies);  k - |I_(n-2)| = {bound}"
              + ("  => C_n > 0" if bound > 0 else ""))

    # n = 7: I_5 <= 1 + 3 J with J = I_4(0,0,L), so C_7 >= k - 1 - 3J > 0 if L(3J) < k - 1
    g4, pos4 = block_positions(4)
    J = snortc.evaluate(g4, [pos4["I(0,0,L)"]], G, trust=True)[0]
    threeJ = G.sum([J, J, J])
    LJ = G.stops(threeJ)[0]
    print(f"\n  n=7: J = I_4(0,0,L) = {G.show(J)};  Left stop of 3J = {LJ} "
          f"< k - 1 = {ks[7] - 1}: {LJ < ks[7] - 1}  => C_7 > 0")
    assert LJ < ks[7] - 1

    print("\nSanity checks with exact values:")
    for n in (3, 4):
        g, _ = apollonian(n)
        a = g.full & ~(1 << 3)
        if n == 3:
            C = Snort(g, G).value(a, g.adj[3] & a, 0)
        else:
            C = snortc.evaluate(g, [(a, g.adj[3] & a, 0)], G, trust=True)[0]
        gi, posi = block_positions(n - 2)
        I = Snort(gi, G).value(*posi["I(0,0,0)"])
        lower = G.add(G.number(ks[n]), I)
        print(f"  n={n}: C_n = {G.show(C)} >= k + I_(n-2) = {ks[n]} + {G.show(I)}: {G.le(lower, C)}")
        assert G.le(lower, C)

    g3, info3 = apollonian(3)
    s3 = Snort(g3, G)
    P = {}
    for v in range(g3.n):
        a = g3.full & ~(1 << v)
        P[v] = s3.value(a, g3.adj[v] & a, 0)
    for v in range(g3.n):
        if info3["level"][v] == 3:
            for x in bits(g3.adj[v]):
                assert G.le(P[v], P[x]) and P[v] != P[x]
    print("  n=3: every level-3 move is strictly below each neighbour's move (exact values): True")

    print("\nWinning first moves (resulting position >= 0, i.e. the opponent loses):")
    for n in (2, 3):
        g, info = apollonian(n)
        s = Snort(g, G)
        seen = {}
        for v in range(g.n):
            a = g.full & ~(1 << v)
            val = s.value(a, g.adj[v] & a, 0)
            key = (info["level"][v], g.degree(v), G.show(val))
            seen.setdefault(key, G.le(G.ZERO, val))
        for (lvl, deg, val), win in sorted(seen.items()):
            print(f"  n={n} level {lvl} (deg {deg}): {val:40s} winning: {win}")


if __name__ == "__main__":
    main()

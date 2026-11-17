"""
Independent checks of the CGT engine and the Snort evaluator.

  * outcome classes predicted from canonical forms are compared with plain
    minimax search on the Snort game tree (no CGT at all);
  * sums: the outcome of a disjoint union of two graphs is compared with the
    outcome of the sum of their canonical values;
  * equality G = H is verified by brute-force search on Snort(G) + (-H), which
    must be a second-player win (this uses only the option structure of H);
  * value with and without component decomposition must coincide;
  * known values and thermographs.

Run:  python3 -m pytest -q tests      (or just  python3 tests/test_engine.py)
"""

import os
import random
import sys
from fractions import Fraction as F

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cgt import Games  # noqa: E402
from snort import Graph, Snort, bits  # noqa: E402
from apollonian import apollonian  # noqa: E402

GAMES = Games()


def random_graph(n, p, rng):
    return Graph(n, [(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < p])


def random_position(graph, rng, k):
    """Play k random legal moves from the empty position."""
    alive, L, R = graph.full, 0, 0
    for _ in range(k):
        left = rng.random() < 0.5
        movable = alive & ~(R if left else L)
        if not movable:
            continue
        v = rng.choice(list(bits(movable)))
        alive &= ~(1 << v)
        if left:
            L |= graph.adj[v]
        else:
            R |= graph.adj[v]
        dead = L & R
        alive &= ~dead
        L &= alive
        R &= alive
    return alive, L, R


class Brute:
    """Plain minimax on Snort (+ optionally an explicit game tree H)."""

    def __init__(self, graph, games=None):
        self.adj = graph.adj
        self.g = games
        self.memo = {}

    def moves(self, alive, L, R, left):
        out = []
        for v in bits(alive & ~(R if left else L)):
            na = alive & ~(1 << v)
            nL, nR = (L | self.adj[v], R) if left else (L, R | self.adj[v])
            dead = nL & nR
            na &= ~dead
            out.append((na, nL & na, nR & na))
        return out

    def wins(self, alive, L, R, h, left):
        """Does the player to move (Left iff left) win from this position?"""
        key = (alive, L, R, h, left)
        r = self.memo.get(key)
        if r is not None:
            return r
        r = False
        for a, l, rr in self.moves(alive, L, R, left):
            if not self.wins(a, l, rr, h, not left):
                r = True
                break
        if not r and h is not None:
            for h2 in (self.g.Lo[h] if left else self.g.Ro[h]):
                if not self.wins(alive, L, R, h2, not left):
                    r = True
                    break
        self.memo[key] = r
        return r

    def outcome(self, alive, L, R, h=None):
        lf = self.wins(alive, L, R, h, True)
        rf = self.wins(alive, L, R, h, False)
        return {(True, True): "N", (True, False): "L", (False, True): "R", (False, False): "P"}[(lf, rf)]


def test_known_values():
    g = GAMES
    for n in range(1, 7):
        K = Graph(n, [(i, j) for i in range(n) for j in range(i + 1, n)])
        v = Snort(K, g).value()
        assert v == (g.STAR if n == 1 else g.switch(g.number(n - 1), g.number(1 - n)))
    for n in range(1, 7):
        S = Graph(n + 1, [(0, i) for i in range(1, n + 1)])
        assert Snort(S, g).value() == g.switch(g.number(n), g.number(-n))


def test_outcomes_random():
    rng = random.Random(1)
    g = GAMES
    for trial in range(300):
        n = rng.randint(1, 9)
        G = random_graph(n, rng.choice([0.2, 0.4, 0.6]), rng)
        s = Snort(G, g)
        alive, L, R = random_position(G, rng, rng.randint(0, 3))
        v = s.value(alive, L, R)
        assert g.outcome(v) == Brute(G).outcome(alive, L, R), (trial, G.edges, alive, L, R)


def test_sums_random():
    rng = random.Random(2)
    g = GAMES
    for trial in range(150):
        n1, n2 = rng.randint(1, 6), rng.randint(1, 6)
        A = random_graph(n1, 0.5, rng)
        B = random_graph(n2, 0.5, rng)
        U = Graph(n1 + n2, A.edges + [(u + n1, v + n1) for u, v in B.edges])
        a1, l1, r1 = random_position(A, rng, rng.randint(0, 2))
        a2, l2, r2 = random_position(B, rng, rng.randint(0, 2))
        va = Snort(A, g).value(a1, l1, r1)
        vb = Snort(B, g).value(a2, l2, r2)
        s = g.add(va, vb)
        out = Brute(U).outcome(a1 | (a2 << n1), l1 | (l2 << n1), r1 | (r2 << n1))
        assert g.outcome(s) == out, trial


def test_equality_by_bruteforce():
    """Snort(G) - value(G) must be a second-player win, for random G."""
    rng = random.Random(3)
    g = GAMES
    for trial in range(60):
        n = rng.randint(2, 8)
        G = random_graph(n, 0.5, rng)
        alive, L, R = random_position(G, rng, rng.randint(0, 2))
        v = Snort(G, g).value(alive, L, R)
        assert Brute(G, g).outcome(alive, L, R, g.neg(v)) == "P", trial
        # and a perturbed value must NOT be equal
        w = g.add(v, g.STAR)
        assert Brute(G, g).outcome(alive, L, R, g.neg(w)) != "P", trial


def test_decomposition_consistency():
    """Splitting into components must not change the value."""
    rng = random.Random(4)
    g = GAMES

    class NoSplit(Snort):
        def components(self, alive, Lt, Rt):
            return [alive] if alive else []

        def _key(self, c, L, R):
            n = self.n
            return c | (L << n) | (R << (2 * n)), False

    for trial in range(60):
        n = rng.randint(2, 8)
        G = random_graph(n, 0.35, rng)
        alive, L, R = random_position(G, rng, rng.randint(0, 2))
        assert Snort(G, g).value(alive, L, R) == NoSplit(G, g, use_symmetry=False).value(alive, L, R)


def test_negation_symmetry():
    g = GAMES
    for d in range(3):
        G, _ = apollonian(d)
        v = Snort(G, g).value()
        assert g.neg(v) == v
        assert g.add(v, v) == g.ZERO


def test_thermographs():
    g = GAMES
    n = g.number
    assert g.temperature(g.switch(n(2), n(-2))) == 2
    assert g.temperature(g.STAR) == 0
    assert g.temperature(g.up()) == 0
    assert g.temperature(n(F(1, 2))) == F(-1, 2)
    assert g.temperature(n(3)) == -1
    h = g.switch(n(2), n(-1))
    assert (g.temperature(h), g.mean(h)) == (F(3, 2), F(1, 2))
    h = g.switch(g.switch(n(4), n(2)), n(0))  # {{4|2}|0}: t = m = 3/2
    assert (g.temperature(h), g.mean(h)) == (F(3, 2), F(3, 2))
    # mean is additive; temperature of a sum is at most the max
    rng = random.Random(5)
    for _ in range(40):
        G = random_graph(rng.randint(2, 7), 0.5, rng)
        H = random_graph(rng.randint(2, 7), 0.5, rng)
        a = Snort(G, g).value(*random_position(G, rng, 1))
        b = Snort(H, g).value(*random_position(H, rng, 1))
        s = g.add(a, b)
        assert g.mean(s) == g.mean(a) + g.mean(b)
        assert g.temperature(s) <= max(g.temperature(a), g.temperature(b))


def test_cpp_backend_agrees():
    """The C++ evaluator must reproduce the Python reference exactly."""
    import shutil
    if shutil.which("g++") is None:
        return
    import snortc
    rng = random.Random(9)
    g = GAMES
    for trial in range(60):
        n = rng.randint(1, 11)
        G = random_graph(n, rng.choice([0.2, 0.4, 0.6]), rng)
        pos = [random_position(G, rng, rng.randint(0, 3)) for _ in range(3)]
        assert snortc.evaluate(G, pos, g) == [Snort(G, g).value(*p) for p in pos], trial
    for d in range(4):
        A, _ = apollonian(d)
        assert snortc.evaluate(A, [(A.full, 0, 0)], g) == [Snort(A, g).value()]


def test_planar3tree_counts():
    """Enumeration reproduces the number of planar 3-trees (OEIS A027610)."""
    from enumerate_3trees import Triangulation
    level = {Triangulation.triangle().code(): Triangulation.triangle()}
    counts = [1]
    for _ in range(6):
        nxt = {}
        for t in level.values():
            for fi in range(len(t.faces)):
                s = t.stack(fi)
                nxt.setdefault(s.code(), s)
        level = nxt
        counts.append(len(level))
    assert counts == [1, 1, 1, 1, 3, 7, 24]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)

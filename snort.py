"""
Snort on graphs, evaluated to canonical form with the engine in cgt.py.

Rules.  Left colours vertices blue, Right colours vertices red; a player may
not colour a vertex adjacent to a vertex of the opponent's colour.  Normal
play: whoever cannot move loses.

Representation.  A position is (alive, Lt, Rt) where `alive` is the bitmask of
uncoloured vertices that can still be coloured by somebody, `Lt` the subset
"tinted" for Left (adjacent to a blue vertex, so only Left may colour it) and
`Rt` the subset tinted for Right.  Coloured vertices are deleted; a vertex
tinted for both players is dead and deleted as well.

Two standard simplifications are applied before evaluation:
  * an edge joining two vertices with the same tint is irrelevant (colouring
    one end only re-tints the other end with the tint it already has), so it is
    ignored;
  * the position is split into connected components (with respect to the
    remaining relevant edges), and its value is the sum of their values.
Components are memoised up to the automorphisms of the host graph and up to
swapping the colours (which negates the value).
"""

from __future__ import annotations

from cgt import Games


def bits(m: int):
    while m:
        b = m & -m
        yield b.bit_length() - 1
        m ^= b


class Graph:
    def __init__(self, n: int, edges):
        self.n = n
        self.adj = [0] * n
        self.edges = sorted({(min(u, v), max(u, v)) for u, v in edges if u != v})
        for u, v in self.edges:
            self.adj[u] |= 1 << v
            self.adj[v] |= 1 << u
        self.full = (1 << n) - 1

    def degree(self, v):
        return bin(self.adj[v]).count("1")

    def automorphisms(self, limit=100000):
        """All automorphisms (as tuples p with p[v] = image of v), by backtracking."""
        n, adj = self.n, self.adj
        deg = [self.degree(v) for v in range(n)]
        # refine colours (1-dim Weisfeiler-Leman) to prune the search
        col = deg[:]
        while True:
            sig = [(col[v], tuple(sorted(col[u] for u in bits(adj[v])))) for v in range(n)]
            ids = {s: i for i, s in enumerate(sorted(set(sig)))}
            new = [ids[s] for s in sig]
            if len(set(new)) == len(set(col)):
                col = new
                break
            col = new
        order = sorted(range(n), key=lambda v: (sum(1 for u in range(n) if col[u] == col[v]), v))
        result = []
        img = [-1] * n
        used = [False] * n

        def ok(v, w):
            for u in bits(adj[v]):
                if img[u] >= 0 and not (adj[w] >> img[u]) & 1:
                    return False
            for u in range(n):
                if img[u] >= 0 and u != v and not (adj[v] >> u) & 1 and (adj[w] >> img[u]) & 1:
                    return False
            return True

        def rec(i):
            if len(result) >= limit:
                return
            if i == n:
                result.append(tuple(img))
                return
            v = order[i]
            for w in range(n):
                if not used[w] and col[w] == col[v] and ok(v, w):
                    img[v] = w
                    used[w] = True
                    rec(i + 1)
                    img[v] = -1
                    used[w] = False

        rec(0)
        return result


class _MaskMapper:
    """Fast image of a bitmask under a fixed vertex permutation (byte tables)."""

    def __init__(self, perm, n):
        nb = (n + 7) // 8
        self.tables = []
        for byte in range(nb):
            tab = [0] * 256
            for val in range(256):
                m = 0
                for k in range(8):
                    if (val >> k) & 1:
                        v = byte * 8 + k
                        if v < n:
                            m |= 1 << perm[v]
                tab[val] = m
            self.tables.append(tab)

    def __call__(self, mask):
        r = 0
        for tab in self.tables:
            r |= tab[mask & 255]
            mask >>= 8
        return r


class Snort:
    def __init__(self, graph: Graph, games: Games | None = None, use_symmetry=True):
        self.G = graph
        self.g = games or Games()
        self.memo: dict[int, int] = {}
        n = graph.n
        self.n = n
        autos = graph.automorphisms() if use_symmetry else [tuple(range(n))]
        self.mappers = [_MaskMapper(p, n) for p in autos if p != tuple(range(n))]
        self.n_autos = len(autos)
        self.stats = {"components": 0}

    # ------------------------------------------------------------------ API
    def value(self, alive=None, Lt=0, Rt=0) -> int:
        """Canonical value of the position."""
        if alive is None:
            alive = self.G.full
        dead = Lt & Rt
        alive &= ~dead
        Lt &= alive
        Rt &= alive
        return self.g.sum(self.component_value(c, Lt & c, Rt & c)
                          for c in self.components(alive, Lt, Rt))

    def components(self, alive, Lt, Rt):
        adj = self.G.adj
        comps = []
        rem = alive
        while rem:
            comp = rem & -rem
            frontier = comp
            while frontier:
                new = 0
                f = frontier
                while f:
                    b = f & -f
                    f ^= b
                    nb = adj[b.bit_length() - 1] & alive
                    if Lt & b:
                        nb &= ~Lt
                    elif Rt & b:
                        nb &= ~Rt
                    new |= nb
                new &= ~comp
                comp |= new
                frontier = new
            comps.append(comp)
            rem &= ~comp
        return comps

    def _key(self, c, L, R):
        n = self.n
        best = c | (L << n) | (R << (2 * n))
        sw = c | (R << n) | (L << (2 * n))
        neg = False
        if sw < best:
            best, neg = sw, True
        for m in self.mappers:
            mc, mL, mR = m(c), m(L), m(R)
            k = mc | (mL << n) | (mR << (2 * n))
            if k < best:
                best, neg = k, False
            k = mc | (mR << n) | (mL << (2 * n))
            if k < best:
                best, neg = k, True
        return best, neg

    def component_value(self, c, L, R) -> int:
        g = self.g
        if c & (c - 1) == 0:  # single vertex
            return g.ONE if L else (g.MINUS_ONE if R else g.STAR)
        key, neg = self._key(c, L, R)
        r = self.memo.get(key)
        if r is None:
            n = self.n
            kc = key & ((1 << n) - 1)
            kL = (key >> n) & ((1 << n) - 1)
            kR = key >> (2 * n)
            r = self._compute(kc, kL, kR)
            self.memo[key] = r
        return g.neg(r) if neg else r

    def options(self, c, L, R, left: bool):
        """Positions (alive, Lt, Rt) reachable by one move of the given player."""
        adj = self.G.adj
        out = []
        movable = c & ~(R if left else L)
        for v in bits(movable):
            na = c & ~(1 << v)
            if left:
                nL = (L | adj[v]) & na
                nR = R & na
            else:
                nL = L & na
                nR = (R | adj[v]) & na
            dead = nL & nR
            na &= ~dead
            out.append((na, nL & ~dead, nR & ~dead, v))
        return out

    def _compute(self, c, L, R) -> int:
        self.stats["components"] += 1
        Ls = {self.value(a, l, r) for a, l, r, _ in self.options(c, L, R, True)}
        Rs = {self.value(a, l, r) for a, l, r, _ in self.options(c, L, R, False)}
        return self.g.canon(Ls, Rs)

    # ------------------------------------------------------------ analysis
    def move_values(self, alive=None, Lt=0, Rt=0, left=True):
        """[(vertex, canonical value of the resulting position)] for each move."""
        if alive is None:
            alive = self.G.full
        return [(v, self.value(a, l, r)) for a, l, r, v in self.options(alive, Lt, Rt, left)]

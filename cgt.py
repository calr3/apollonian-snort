"""
A small, self-contained engine for short partizan combinatorial games.

Games are stored in *canonical form* and hash-consed: every canonical game is
an integer id, and two ids are equal iff the games are equal.  The engine
supports

  * construction of canonical forms from arbitrary option sets
    (removal of dominated options and bypassing of reversible options),
  * comparison (<=), negation and disjunctive sum,
  * dyadic-rational numbers with fast paths,
  * thermographs (left/right walls as piecewise-linear functions), from which
    temperature, mean and stops are read off,
  * pretty printing in the usual notation (numbers, nimbers, x*n, up-multiples,
    switches x±y, and nested {L|R}).

Only standard theory is used; see e.g. A. N. Siegel, *Combinatorial Game
Theory*, AMS GSM 146 (2013), chapters II (canonical forms) and II.5
(thermography).
"""

from __future__ import annotations

import sys
from fractions import Fraction

sys.setrecursionlimit(1_000_000)

_SHIFT = 32


def _is_dyadic(q: Fraction) -> bool:
    d = q.denominator
    return d & (d - 1) == 0


def simplest_between(lo, hi):
    """Simplest number x with lo < x < hi (lo/hi may be None = -inf/+inf)."""
    if lo is not None and hi is not None and not lo < hi:
        raise ValueError("empty interval")
    # integers first
    if (lo is None or lo < 0) and (hi is None or hi > 0):
        return Fraction(0)
    if lo is not None and lo >= 0:
        n = Fraction(int(lo) + 1)  # smallest integer > lo  (lo >= 0)
        if hi is None or n < hi:
            return n
    if hi is not None and hi <= 0:
        n = Fraction(-int(-hi) - 1)  # largest integer < hi (hi <= 0)
        if lo is None or n > lo:
            return n
    # interval lies strictly between two consecutive integers -> dyadic search
    denom = 2
    while True:
        # smallest numerator m with m/denom > lo
        m = (lo * denom).__floor__() + 1
        x = Fraction(m, denom)
        if x < hi:
            return x
        denom *= 2


class Games:
    """Universe of canonical short games."""

    def __init__(self):
        self.Lo: list[tuple[int, ...]] = []
        self.Ro: list[tuple[int, ...]] = []
        self.nv: list[Fraction | None] = []  # numeric value, if a number
        self.index: dict[tuple, int] = {}
        self._le: dict[int, bool] = {}
        self._add: dict[int, int] = {}
        self._neg: dict[int, int] = {}
        self._num: dict[Fraction, int] = {}
        self._thermo: dict[int, "Thermograph"] = {}
        self._nim: dict[int, int | None] = {}
        self.ZERO = self._intern((), ())
        self._num[Fraction(0)] = self.ZERO
        self.STAR = self._intern((self.ZERO,), (self.ZERO,))
        self.ONE = self.number(1)
        self.MINUS_ONE = self.number(-1)

    # ------------------------------------------------------------------ core
    def _intern(self, Lt: tuple, Rt: tuple) -> int:
        key = (Lt, Rt)
        g = self.index.get(key)
        if g is not None:
            return g
        g = len(self.Lo)
        self.Lo.append(Lt)
        self.Ro.append(Rt)
        self.nv.append(self._numval(Lt, Rt))
        self.index[key] = g
        return g

    def _numval(self, Lt, Rt):
        """Value if the canonical form {Lt|Rt} is a number, else None."""
        if len(Lt) > 1 or len(Rt) > 1:
            return None
        lo = hi = None
        if Lt:
            lo = self.nv[Lt[0]]
            if lo is None:
                return None
        if Rt:
            hi = self.nv[Rt[0]]
            if hi is None:
                return None
        if lo is not None and hi is not None and not lo < hi:
            return None
        return simplest_between(lo, hi)

    def number(self, q) -> int:
        q = Fraction(q)
        g = self._num.get(q)
        if g is not None:
            return g
        if not _is_dyadic(q):
            raise ValueError(f"{q} is not a dyadic rational")
        if q.denominator == 1:
            if q > 0:
                g = self._intern((self.number(q - 1),), ())
            else:
                g = self._intern((), (self.number(q + 1),))
        else:
            e = Fraction(1, q.denominator)
            g = self._intern((self.number(q - e),), (self.number(q + e),))
        self._num[q] = g
        return g

    def is_number(self, g) -> bool:
        return self.nv[g] is not None

    # ----------------------------------------------------------- comparison
    def le(self, x: int, y: int) -> bool:
        """x <= y."""
        if x == y:
            return True
        nv = self.nv
        nx, ny = nv[x], nv[y]
        if nx is not None and ny is not None:
            return nx <= ny
        key = (x << _SHIFT) | y
        r = self._le.get(key)
        if r is not None:
            return r
        r = True
        le = self.le
        for yr in self.Ro[y]:
            if le(yr, x):
                r = False
                break
        if r:
            for xl in self.Lo[x]:
                if le(y, xl):
                    r = False
                    break
        self._le[key] = r
        return r

    def ge(self, x, y):
        return self.le(y, x)

    def lt(self, x, y):
        return x != y and self.le(x, y)

    def fuzzy(self, x, y):
        return not self.le(x, y) and not self.le(y, x)

    def outcome(self, g) -> str:
        """'L', 'R', 'P' (second player wins) or 'N' (first player wins)."""
        z = self.ZERO
        ge0 = self.le(z, g)
        le0 = self.le(g, z)
        if ge0 and le0:
            return "P"
        if ge0:
            return "L"
        if le0:
            return "R"
        return "N"

    # -------------------------------------------------------- canonical form
    def canon(self, Ls, Rs) -> int:
        """Canonical form of {Ls | Rs}; Ls, Rs are iterables of canonical ids."""
        Ls = set(Ls)
        Rs = set(Rs)
        Lo, Ro, le = self.Lo, self.Ro, self.le
        while True:
            Ls = self._extreme(Ls, left=True)
            Rs = self._extreme(Rs, left=False)
            form = _Form(self, Ls, Rs)
            changed = False
            newL = []
            for A in Ls:
                for AR in Ro[A]:
                    if form.x_le_G(AR):  # A reversible through AR
                        newL.extend(Lo[AR])
                        changed = True
                        break
                else:
                    newL.append(A)
            newR = []
            for B in Rs:
                for BL in Lo[B]:
                    if form.G_le_y(BL):  # B reversible through BL
                        newR.extend(Ro[BL])
                        changed = True
                        break
                else:
                    newR.append(B)
            if not changed:
                break
            Ls, Rs = set(newL), set(newR)
        return self._intern(tuple(sorted(Ls)), tuple(sorted(Rs)))

    def _extreme(self, S, left: bool):
        """Keep the maximal (left) or minimal (right) elements of S."""
        if len(S) <= 1:
            return S
        items = list(S)
        nv = self.nv
        # fast path: all numbers -> single extreme
        if all(nv[i] is not None for i in items):
            return {max(items, key=nv.__getitem__) if left else min(items, key=nv.__getitem__)}
        le = self.le
        keep = set()
        for a in items:
            dominated = False
            for b in items:
                if b != a and (le(a, b) if left else le(b, a)):
                    dominated = True
                    break
            if not dominated:
                keep.add(a)
        return keep

    # ------------------------------------------------------------ arithmetic
    def neg(self, g: int) -> int:
        r = self._neg.get(g)
        if r is not None:
            return r
        if self.nv[g] is not None:
            r = self.number(-self.nv[g])
        else:
            r = self._intern(tuple(sorted(self.neg(x) for x in self.Ro[g])),
                             tuple(sorted(self.neg(x) for x in self.Lo[g])))
        self._neg[g] = r
        self._neg[r] = g
        return r

    def add(self, x: int, y: int) -> int:
        Z = self.ZERO
        if x == Z:
            return y
        if y == Z:
            return x
        if x > y:
            x, y = y, x
        key = (x << _SHIFT) | y
        r = self._add.get(key)
        if r is not None:
            return r
        nx, ny = self.nv[x], self.nv[y]
        add = self.add
        if nx is not None and ny is not None:
            r = self.number(nx + ny)
        elif nx is not None:  # number translation
            r = self.canon([add(a, x) for a in self.Lo[y]], [add(a, x) for a in self.Ro[y]])
        elif ny is not None:
            r = self.canon([add(a, y) for a in self.Lo[x]], [add(a, y) for a in self.Ro[x]])
        else:
            Ls = [add(a, y) for a in self.Lo[x]] + [add(x, a) for a in self.Lo[y]]
            Rs = [add(a, y) for a in self.Ro[x]] + [add(x, a) for a in self.Ro[y]]
            r = self.canon(Ls, Rs)
        self._add[key] = r
        return r

    def sub(self, x, y):
        return self.add(x, self.neg(y))

    def sum(self, gs) -> int:
        gs = list(gs)
        # combine numbers first (cheap), then the rest in a fixed order
        num = Fraction(0)
        rest = []
        for g in gs:
            v = self.nv[g]
            if v is not None:
                num += v
            else:
                rest.append(g)
        rest.sort()
        r = self.number(num)
        for g in rest:
            r = self.add(r, g)
        return r

    def switch(self, a, b):
        """The game {a | b} (canonicalised)."""
        return self.canon([a], [b])

    # ---------------------------------------------------------- inspection
    def birthday(self, g, _memo={}):
        key = (id(self), g)
        r = _memo.get(key)
        if r is None:
            opts = self.Lo[g] + self.Ro[g]
            r = 0 if not opts else 1 + max(self.birthday(o) for o in opts)
            _memo[key] = r
        return r

    def size(self, g) -> int:
        """Number of distinct canonical subpositions (a measure of complexity)."""
        seen = set()
        stack = [g]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            stack.extend(self.Lo[x])
            stack.extend(self.Ro[x])
        return len(seen)

    def nimber(self, g):
        """n if g == *n, else None."""
        if g in self._nim:
            return self._nim[g]
        r = None
        if g == self.ZERO:
            r = 0
        elif self.Lo[g] == self.Ro[g]:
            ks = sorted(self.nimber(x) if self.nimber(x) is not None else -1 for x in self.Lo[g])
            if ks == list(range(len(ks))):
                r = len(ks)
        self._nim[g] = r
        return r

    def star(self, n: int) -> int:
        opts = [self.star(k) for k in range(n)] if n else []
        return self.canon(opts, opts)

    def up(self) -> int:
        return self.canon([self.ZERO], [self.STAR])

    # ------------------------------------------------------- thermography
    def thermograph(self, g) -> "Thermograph":
        th = self._thermo.get(g)
        if th is not None:
            return th
        v = self.nv[g]
        if v is not None:
            if v.denominator == 1:
                temp = Fraction(-1)
            else:
                temp = Fraction(-1, v.denominator)
            th = Thermograph(PL.const(v), PL.const(v), temp, v)
        else:
            LS = PL.maximum([self.thermograph(a).right.shear(-1) for a in self.Lo[g]])
            RS = PL.minimum([self.thermograph(a).left.shear(+1) for a in self.Ro[g]])
            t = PL.first_le(LS, RS)  # first t >= -1 with LS(t) <= RS(t)
            m = LS(t)
            th = Thermograph(LS.truncate(t, m), RS.truncate(t, m), t, m)
        self._thermo[g] = th
        return th

    def temperature(self, g) -> Fraction:
        return self.thermograph(g).temperature

    def mean(self, g) -> Fraction:
        return self.thermograph(g).mean

    def stops(self, g):
        """(Left stop, Right stop)."""
        return self._stop(g, True), self._stop(g, False)

    def _stop(self, g, left, _memo={}):
        key = (id(self), g, left)
        if key in _memo:
            return _memo[key]
        v = self.nv[g]
        if v is not None:
            r = v
        elif left:
            r = max(self._stop(a, False) for a in self.Lo[g])
        else:
            r = min(self._stop(a, True) for a in self.Ro[g])
        _memo[key] = r
        return r

    # --------------------------------------------------------------- output
    def show(self, g) -> str:
        return self._show(g, {})

    def _show(self, g, memo):
        if g in memo:
            return memo[g]
        s = self._show_special(g, memo)
        if s is None:
            Ls = ", ".join(self._show(a, memo) for a in self.Lo[g])
            Rs = ", ".join(self._show(a, memo) for a in self.Ro[g])
            s = "{" + Ls + " | " + Rs + "}"
        memo[g] = s
        return s

    def _show_special(self, g, memo):
        v = self.nv[g]
        if v is not None:
            return _fmt_num(v)
        n = self.nimber(g)
        if n is not None:
            return "*" if n == 1 else f"*{n}"
        Lo, Ro = self.Lo[g], self.Ro[g]
        # x + *n  (number plus nimber, n >= 1)
        if Lo == Ro:
            nums = [self.nv[a] for a in Lo if self.nv[a] is not None]
            if len(nums) == 1:
                x = nums[0]
                xg = self.number(x)
                k = self.nimber(self.sub(g, xg))
                if k is not None and k >= 1:
                    return _fmt_num(x) + ("*" if k == 1 else f"*{k}")
        # up-multiples (with optional star) around a number: x + n.up (+*)
        u = self._as_up_multiple(g)
        if u is not None:
            x, k, st = u
            arrow = "↑" if k > 0 else "↓"
            m = abs(k)
            core = arrow if m == 1 else ("⇑" if k > 0 else "⇓") if m == 2 else f"{m}{arrow}"
            pre = "" if x == 0 else _fmt_num(x)
            return pre + core + ("*" if st else "")
        # switches  x ± y  with number options
        if len(Lo) == 1 and len(Ro) == 1:
            a, b = self.nv[Lo[0]], self.nv[Ro[0]]
            if a is not None and b is not None and a > b:
                c, d = (a + b) / 2, (a - b) / 2
                return ("" if c == 0 else _fmt_num(c)) + "±" + _fmt_num(d)
            # x ± G where G is a non-number game: {x+G | x-G}
            l, r = Lo[0], Ro[0]
            # centre c = mean of the thermograph is a natural candidate
            c = self.mean(g)
            if _is_dyadic(c):
                cg = self.number(c)
                gl = self.sub(l, cg)
                if self.neg(gl) == self.sub(r, cg) and not self.is_number(gl) and self.le(self.ZERO, gl):
                    inner = self._show(gl, memo)
                    return ("" if c == 0 else _fmt_num(c)) + "±(" + inner + ")"
        return None

    def _as_up_multiple(self, g, maxk=12):
        """Return (x, k, star) if g == x + k.up (+ * if star), |k| <= maxk, k != 0."""
        if self.mean(g) is None:
            return None
        x = self.mean(g)
        if not _is_dyadic(x):
            return None
        L, R = self.stops(g)
        if L != x or R != x:
            return None
        h = self.sub(g, self.number(x))
        if not hasattr(self, "_upm"):
            up = self.up()
            self._upm = {}
            acc_p, acc_n = self.ZERO, self.ZERO
            for k in range(1, maxk + 1):
                acc_p = self.add(acc_p, up)
                acc_n = self.add(acc_n, self.neg(up))
                self._upm[acc_p] = (k, False)
                self._upm[self.add(acc_p, self.STAR)] = (k, True)
                self._upm[acc_n] = (-k, False)
                self._upm[self.add(acc_n, self.STAR)] = (-k, True)
        r = self._upm.get(h)
        if r is None:
            return None
        return (x, r[0], r[1])


def _fmt_num(v: Fraction) -> str:
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


class _Form:
    """Comparisons against a (possibly non-canonical) form G = {Ls | Rs}."""

    __slots__ = ("g", "Ls", "Rs", "m1", "m2")

    def __init__(self, g: Games, Ls, Rs):
        self.g, self.Ls, self.Rs = g, Ls, Rs
        self.m1: dict[int, bool] = {}
        self.m2: dict[int, bool] = {}

    def x_le_G(self, x: int) -> bool:
        r = self.m1.get(x)
        if r is not None:
            return r
        g = self.g
        r = True
        for gr in self.Rs:
            if g.le(gr, x):
                r = False
                break
        if r:
            for xl in g.Lo[x]:
                if self.G_le_y(xl):
                    r = False
                    break
        self.m1[x] = r
        return r

    def G_le_y(self, y: int) -> bool:
        r = self.m2.get(y)
        if r is not None:
            return r
        g = self.g
        r = True
        for gl in self.Ls:
            if g.le(y, gl):
                r = False
                break
        if r:
            for yr in g.Ro[y]:
                if self.x_le_G(yr):
                    r = False
                    break
        self.m2[y] = r
        return r


# ----------------------------------------------------------------------------
# Piecewise-linear functions on [-1, oo) used for thermograph walls
# ----------------------------------------------------------------------------

class PL:
    """Continuous piecewise-linear function on [-1, oo).

    pts: list of (t, v) with strictly increasing t, pts[0][0] == -1;
    linear between consecutive points, slope `tail` after the last point.
    """

    __slots__ = ("pts", "tail")

    def __init__(self, pts, tail):
        self.pts = pts
        self.tail = Fraction(tail)

    @staticmethod
    def const(v):
        return PL([(Fraction(-1), Fraction(v))], 0)

    def __call__(self, t):
        pts = self.pts
        if t >= pts[-1][0]:
            return pts[-1][1] + self.tail * (t - pts[-1][0])
        for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
            if t0 <= t <= t1:
                return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
        raise ValueError(t)

    def slope_after(self, t):
        pts = self.pts
        if t >= pts[-1][0]:
            return self.tail
        for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
            if t0 <= t < t1:
                return (v1 - v0) / (t1 - t0)
        raise ValueError(t)

    def shear(self, s):
        """t -> f(t) + s*t."""
        return PL([(t, v + s * t) for t, v in self.pts], self.tail + s)

    def truncate(self, t, m):
        """Agree with self on [-1, t] and equal the constant m afterwards."""
        pts = [(a, b) for a, b in self.pts if a < t]
        pts.append((t, m))
        return PL(_simplify(pts), 0)

    @staticmethod
    def _breaks(fs):
        ts = sorted({t for f in fs for t, _ in f.pts})
        return ts

    @staticmethod
    def _combine(fs, pick):
        if len(fs) == 1:
            return fs[0]
        ts = PL._breaks(fs)
        # add pairwise crossing points inside each interval and in the tail
        cand = set(ts)
        bounds = ts + [ts[-1] + 1]
        for i in range(len(bounds) - 1):
            a, b = bounds[i], bounds[i + 1]
            last = i == len(bounds) - 2
            vals_a = [(f(a), f.slope_after(a)) for f in fs]
            for j in range(len(fs)):
                for k in range(j + 1, len(fs)):
                    (va, sa), (vb, sb) = vals_a[j], vals_a[k]
                    if sa != sb:
                        x = a + (vb - va) / (sa - sb)
                        if x > a and (last or x < b):
                            cand.add(x)
        ts = sorted(cand)
        pts = [(t, pick(f(t) for f in fs)) for t in ts]
        tl = ts[-1]
        vals = [(f(tl), f.slope_after(tl)) for f in fs]
        best = pick(v for v, _ in vals)
        slopes = [s for v, s in vals if v == best]
        tail = pick(slopes)
        return PL(_simplify(pts), tail)

    @staticmethod
    def maximum(fs):
        return PL._combine(list(fs), max)

    @staticmethod
    def minimum(fs):
        return PL._combine(list(fs), min)

    @staticmethod
    def first_le(f, g):
        """Smallest t >= -1 with f(t) <= g(t) (f - g is non-increasing for scaffolds)."""
        ts = sorted({t for t, _ in f.pts} | {t for t, _ in g.pts})
        prev = None
        for t in ts:
            if f(t) <= g(t):
                if prev is None:
                    return t
                # crossing in (prev, t]
                fa, ga = f(prev), g(prev)
                sf, sg = f.slope_after(prev), g.slope_after(prev)
                return prev + (fa - ga) / (sg - sf)
            prev = t
        t = ts[-1]
        fa, ga = f(t), g(t)
        sf, sg = f.tail, g.tail
        if sf >= sg:
            raise ValueError("scaffolds never meet")
        return t + (fa - ga) / (sg - sf)

    def __repr__(self):
        return f"PL({[(str(t), str(v)) for t, v in self.pts]}, tail={self.tail})"


def _simplify(pts):
    out = []
    for p in pts:
        if out and out[-1][0] == p[0]:
            continue
        out.append(p)
        while len(out) >= 3:
            (t0, v0), (t1, v1), (t2, v2) = out[-3:]
            if (v1 - v0) * (t2 - t1) == (v2 - v1) * (t1 - t0):
                del out[-2]
            else:
                break
    return out


class Thermograph:
    __slots__ = ("left", "right", "temperature", "mean")

    def __init__(self, left: PL, right: PL, temperature, mean):
        self.left, self.right = left, right
        self.temperature = temperature
        self.mean = mean

    def __repr__(self):
        return (f"Thermograph(t={self.temperature}, m={self.mean}, "
                f"L={self.left}, R={self.right})")

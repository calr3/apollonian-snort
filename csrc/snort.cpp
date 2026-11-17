// Fast Snort evaluator: canonical forms of short partizan games + Snort on
// graphs with up to 64 vertices.  Algorithmically identical to cgt.py /
// snort.py (which are the reference implementation); this exists only for
// speed.  The result is written as a DAG of canonical games that cgt.py can
// import (see snortc.py).
//
// Input (stdin):
//   n m
//   m lines "u v"
//   k                      number of automorphisms (excluding identity is fine)
//   k lines of n integers  vertex permutations
//   q                      number of positions to evaluate
//   q lines "alive L R"    bitmasks (decimal)
// Output (stdout):
//   "ROOTS id1 ... idq"
//   then, children before parents, one line per canonical game:
//   "N id num exp"         the dyadic number num / 2^exp
//   "G id nL l1..lnL nR r1..rnR"
// Progress is reported on stderr.
//
// Build: g++ -O2 -std=c++17 -o snortc snort.cpp

#include <bits/stdc++.h>
#if defined(__BMI2__)
#include <immintrin.h>
#endif
using namespace std;
typedef uint64_t u64;
typedef int64_t i64;
typedef uint32_t u32;
#ifndef LE_CACHE_LOG
#define LE_CACHE_LOG 27
#endif

// ---------------------------------------------------------------- dyadics
struct Dy {
    i64 n;
    int e;  // value n / 2^e ; normalised: e == 0 or n odd
};
static Dy mkdy(i64 n, int e) {
    while (e > 0 && (n % 2 == 0)) { n /= 2; e--; }
    if (n == 0) e = 0;
    return {n, e};
}
static int dcmp(Dy a, Dy b) {
    int e = max(a.e, b.e);
    __int128 x = (__int128)a.n << (e - a.e), y = (__int128)b.n << (e - b.e);
    return x < y ? -1 : (x > y ? 1 : 0);
}
static Dy dadd(Dy a, Dy b) {
    int e = max(a.e, b.e);
    return mkdy((a.n << (e - a.e)) + (b.n << (e - b.e)), e);
}
static i64 dfloor(Dy a) { return a.e == 0 ? a.n : (a.n >> a.e); }  // arithmetic shift = floor
static Dy simplest(bool hasLo, Dy lo, bool hasHi, Dy hi) {
    Dy zero{0, 0};
    if ((!hasLo || dcmp(lo, zero) < 0) && (!hasHi || dcmp(hi, zero) > 0)) return zero;
    if (hasLo && dcmp(lo, zero) >= 0) {
        Dy c{dfloor(lo) + 1, 0};
        if (!hasHi || dcmp(c, hi) < 0) return c;
    }
    if (hasHi && dcmp(hi, zero) <= 0) {
        Dy nh{-hi.n, hi.e};
        Dy c{-(dfloor(nh) + 1), 0};
        if (!hasLo || dcmp(c, lo) > 0) return c;
    }
    for (int e = 1; e < 60; e++) {
        // smallest m with m/2^e > lo
        i64 m;
        if (lo.e <= e) m = (lo.n << (e - lo.e)) + 1;
        else m = (lo.n >> (lo.e - e)) + 1;
        Dy x = mkdy(m, e);
        if (dcmp(x, hi) < 0) return x;
    }
    fprintf(stderr, "simplest: failure\n");
    exit(1);
}

// ------------------------------------------------------------ hash tables
// open addressing u64 -> int32 (value -1 = absent)
struct Map64 {
    vector<u64> keys;
    vector<int32_t> vals;
    size_t cnt = 0, mask;
    static constexpr u64 EMPTY = ~0ULL;
    Map64(size_t cap = 1 << 16) { keys.assign(cap, (u64)EMPTY); vals.assign(cap, 0); mask = cap - 1; }
    static inline u64 h(u64 k) {
        k ^= k >> 33; k *= 0xff51afd7ed558ccdULL; k ^= k >> 33; k *= 0xc4ceb9fe1a85ec53ULL; k ^= k >> 33;
        return k;
    }
    inline int get(u64 k) const {
        size_t i = h(k) & mask;
        while (true) {
            if (keys[i] == k) return vals[i];
            if (keys[i] == EMPTY) return -1;
            i = (i + 1) & mask;
        }
    }
    void put(u64 k, int v) {
        if ((cnt + 1) * 2 > keys.size()) grow();
        size_t i = h(k) & mask;
        while (keys[i] != EMPTY && keys[i] != k) i = (i + 1) & mask;
        if (keys[i] == EMPTY) cnt++;
        keys[i] = k; vals[i] = v;
    }
    void grow() {
        vector<u64> ok; vector<int32_t> ov;
        ok.swap(keys); ov.swap(vals);
        keys.assign(ok.size() * 2, (u64)EMPTY); vals.assign(ok.size() * 2, 0); mask = keys.size() - 1; cnt = 0;
        for (size_t i = 0; i < ok.size(); i++) if (ok[i] != EMPTY) put(ok[i], ov[i]);
    }
};


// fixed-size 2-way set-associative cache u64 -> bool (lossy; for <= memo)
struct Cache64 {
    vector<u64> keys;
    vector<uint8_t> vals;
    size_t mask;
    size_t cnt = 0;
    static constexpr u64 EMPTY = ~0ULL;
    explicit Cache64(int logsize) {
        keys.assign((size_t)1 << logsize, (u64)EMPTY);
        vals.assign((size_t)1 << logsize, 0);
        mask = ((size_t)1 << logsize) - 1;
    }
    inline int get(u64 k) const {
        size_t i = Map64::h(k) & mask & ~(size_t)1;
        if (keys[i] == k) return vals[i];
        if (keys[i + 1] == k) return vals[i + 1];
        return -1;
    }
    inline void put(u64 k, bool v) {
        size_t i = Map64::h(k) & mask & ~(size_t)1;
        if (keys[i] == EMPTY || keys[i] == k) { if (keys[i] == EMPTY) cnt++; keys[i] = k; vals[i] = v; return; }
        if (keys[i + 1] == EMPTY) cnt++;
        keys[i + 1] = keys[i]; vals[i + 1] = vals[i];
        keys[i] = k; vals[i] = v;
    }
};

// ------------------------------------------------------------------ games
struct Node {
    uint32_t lo, ro;
    uint16_t nl, nr;
    bool isnum;
    Dy v;
};

struct Games {
    vector<Node> N;
    vector<int> pool;
    vector<int32_t> idx;  // open-addressing table of node ids keyed by option hash
    size_t idxMask = 0, idxCount = 0;
    map<pair<i64, int>, int> nums;
    Cache64 leMemo{LE_CACHE_LOG};
    Map64 addMemo{1 << 18};
    vector<int> negMemo;
    int ZERO, STAR, ONE, MONE;

    Games() {
        idx.assign(1 << 16, -1);
        idxMask = idx.size() - 1;
        ZERO = intern({}, {});
        nums[{0, 0}] = ZERO;
        STAR = intern({ZERO}, {ZERO});
        ONE = number({1, 0});
        MONE = number({-1, 0});
    }
    inline const int* L(int g) const { return pool.data() + N[g].lo; }
    inline const int* R(int g) const { return pool.data() + N[g].ro; }
    vector<int> Lv(int g) const { return vector<int>(L(g), L(g) + N[g].nl); }
    vector<int> Rv(int g) const { return vector<int>(R(g), R(g) + N[g].nr); }

    static u64 hashArr(const int* a, size_t na, const int* b, size_t nb) {
        u64 h = 1469598103934665603ULL;
        for (size_t i = 0; i < na; i++) { h ^= (u64)a[i] + 0x9e3779b97f4a7c15ULL; h *= 1099511628211ULL; h ^= h >> 29; }
        h ^= 0xabcdef12345ULL; h *= 1099511628211ULL;
        for (size_t i = 0; i < nb; i++) { h ^= (u64)b[i] + 0x7f4a7c159e3779b9ULL; h *= 1099511628211ULL; h ^= h >> 29; }
        return Map64::h(h);
    }
    static u64 hashOpts(const vector<int>& a, const vector<int>& b) {
        return hashArr(a.data(), a.size(), b.data(), b.size());
    }
    void rehashIndex() {
        vector<int32_t> nidx(idx.size() * 2, -1);
        size_t m = nidx.size() - 1;
        for (size_t g = 0; g < N.size(); g++) {
            size_t i = hashArr(L(g), N[g].nl, R(g), N[g].nr) & m;
            while (nidx[i] >= 0) i = (i + 1) & m;
            nidx[i] = g;
        }
        idx.swap(nidx);
        idxMask = m;
    }
    bool sameOpts(int g, const vector<int>& a, const vector<int>& b) const {
        if (N[g].nl != a.size() || N[g].nr != b.size()) return false;
        for (size_t i = 0; i < a.size(); i++) if (L(g)[i] != a[i]) return false;
        for (size_t i = 0; i < b.size(); i++) if (R(g)[i] != b[i]) return false;
        return true;
    }
    // a, b must be sorted & unique
    int intern(const vector<int>& a, const vector<int>& b) {
        u64 h = hashOpts(a, b);
        size_t slot = h & idxMask;
        while (idx[slot] >= 0) {
            if (sameOpts(idx[slot], a, b)) return idx[slot];
            slot = (slot + 1) & idxMask;
        }
        Node nd;
        nd.lo = pool.size(); pool.insert(pool.end(), a.begin(), a.end());
        nd.ro = pool.size(); pool.insert(pool.end(), b.begin(), b.end());
        nd.nl = a.size(); nd.nr = b.size();
        nd.isnum = false; nd.v = {0, 0};
        // number?
        if (a.size() <= 1 && b.size() <= 1) {
            bool ok = true;
            bool hl = !a.empty(), hr = !b.empty();
            Dy lo{0, 0}, hi{0, 0};
            if (hl) { if (!N[a[0]].isnum) ok = false; else lo = N[a[0]].v; }
            if (hr) { if (!N[b[0]].isnum) ok = false; else hi = N[b[0]].v; }
            if (ok && hl && hr && dcmp(lo, hi) >= 0) ok = false;
            if (ok) { nd.isnum = true; nd.v = simplest(hl, lo, hr, hi); }
        }
        int g = N.size();
        N.push_back(nd);
        idx[slot] = g;
        if (++idxCount * 2 > idx.size()) rehashIndex();
        return g;
    }
    int number(Dy q) {
        auto it = nums.find({q.n, q.e});
        if (it != nums.end()) return it->second;
        int g;
        if (q.e == 0) {
            if (q.n > 0) g = intern({number({q.n - 1, 0})}, {});
            else g = intern({}, {number({q.n + 1, 0})});
        } else {
            int a = number(mkdy(q.n - 1, q.e)), b = number(mkdy(q.n + 1, q.e));
            g = intern({a}, {b});
        }
        nums[{q.n, q.e}] = g;
        return g;
    }

    bool le(int x, int y) {
        if (x == y) return true;
        const Node &nx = N[x], &ny = N[y];
        if (nx.isnum && ny.isnum) return dcmp(nx.v, ny.v) <= 0;
        u64 key = ((u64)x << 32) | (u32)y;
        int m = leMemo.get(key);
        if (m >= 0) return m;
        bool r = true;
        {
            int nr = N[y].nr; uint32_t ro = N[y].ro;
            for (int i = 0; i < nr; i++) if (le(pool[ro + i], x)) { r = false; break; }
        }
        if (r) {
            int nl = N[x].nl; uint32_t lo = N[x].lo;
            for (int i = 0; i < nl; i++) if (le(y, pool[lo + i])) { r = false; break; }
        }
        leMemo.put(key, r);
        return r;
    }

    // comparisons with a non-canonical form {Ls|Rs}
    struct Form {
        Games* g;
        const vector<int>&Ls, &Rs;
        unordered_map<int, bool> m1, m2;
        Form(Games* g_, const vector<int>& a, const vector<int>& b) : g(g_), Ls(a), Rs(b) {}
        bool xleG(int x) {
            auto it = m1.find(x);
            if (it != m1.end()) return it->second;
            bool r = true;
            for (int gr : Rs) if (g->le(gr, x)) { r = false; break; }
            if (r) {
                vector<int> xl = g->Lv(x);
                for (int a : xl) if (Gley(a)) { r = false; break; }
            }
            m1[x] = r;
            return r;
        }
        bool Gley(int y) {
            auto it = m2.find(y);
            if (it != m2.end()) return it->second;
            bool r = true;
            for (int gl : Ls) if (g->le(y, gl)) { r = false; break; }
            if (r) {
                vector<int> yr = g->Rv(y);
                for (int a : yr) if (xleG(a)) { r = false; break; }
            }
            m2[y] = r;
            return r;
        }
    };

    void extreme(vector<int>& S, bool left) {
        sort(S.begin(), S.end());
        S.erase(unique(S.begin(), S.end()), S.end());
        if (S.size() <= 1) return;
        bool allnum = true;
        for (int x : S) if (!N[x].isnum) { allnum = false; break; }
        if (allnum) {
            int best = S[0];
            for (int x : S) {
                int c = dcmp(N[x].v, N[best].v);
                if (left ? c > 0 : c < 0) best = x;
            }
            S.assign(1, best);
            return;
        }
        vector<int> keep;
        for (int a : S) {
            bool dom = false;
            for (int b : S)
                if (b != a && (left ? le(a, b) : le(b, a))) { dom = true; break; }
            if (!dom) keep.push_back(a);
        }
        S.swap(keep);
    }

    int canon(vector<int> Ls, vector<int> Rs) {
        while (true) {
            extreme(Ls, true);
            extreme(Rs, false);
            Form f(this, Ls, Rs);
            bool changed = false;
            vector<int> nL, nR;
            for (int A : Ls) {
                bool rev = false;
                vector<int> ar = Rv(A);
                for (int AR : ar)
                    if (f.xleG(AR)) {
                        vector<int> x = Lv(AR);
                        nL.insert(nL.end(), x.begin(), x.end());
                        rev = changed = true;
                        break;
                    }
                if (!rev) nL.push_back(A);
            }
            for (int B : Rs) {
                bool rev = false;
                vector<int> bl = Lv(B);
                for (int BL : bl)
                    if (f.Gley(BL)) {
                        vector<int> x = Rv(BL);
                        nR.insert(nR.end(), x.begin(), x.end());
                        rev = changed = true;
                        break;
                    }
                if (!rev) nR.push_back(B);
            }
            if (!changed) break;
            Ls.swap(nL);
            Rs.swap(nR);
        }
        return intern(Ls, Rs);
    }

    int neg(int g) {
        if ((size_t)g < negMemo.size() && negMemo[g] >= 0) return negMemo[g];
        int r;
        if (N[g].isnum) r = number({-N[g].v.n, N[g].v.e});
        else {
            vector<int> a, b;
            for (int x : Rv(g)) a.push_back(neg(x));
            for (int x : Lv(g)) b.push_back(neg(x));
            sort(a.begin(), a.end()); sort(b.begin(), b.end());
            r = intern(a, b);
        }
        if (negMemo.size() < N.size()) negMemo.resize(N.size() * 2 + 16, -1);
        negMemo[g] = r; negMemo[r] = g;
        return r;
    }

    int add(int x, int y) {
        if (x == ZERO) return y;
        if (y == ZERO) return x;
        if (x > y) swap(x, y);
        u64 key = ((u64)x << 32) | (u32)y;
        int m = addMemo.get(key);
        if (m >= 0) return m;
        int r;
        bool nx = N[x].isnum, ny = N[y].isnum;
        if (nx && ny) r = number(dadd(N[x].v, N[y].v));
        else if (nx || ny) {
            int num = nx ? x : y, g = nx ? y : x;
            vector<int> Ls, Rs;
            for (int a : Lv(g)) Ls.push_back(add(a, num));
            for (int a : Rv(g)) Rs.push_back(add(a, num));
            r = canon(Ls, Rs);
        } else {
            vector<int> Ls, Rs;
            for (int a : Lv(x)) Ls.push_back(add(a, y));
            for (int a : Lv(y)) Ls.push_back(add(x, a));
            for (int a : Rv(x)) Rs.push_back(add(a, y));
            for (int a : Rv(y)) Rs.push_back(add(x, a));
            r = canon(Ls, Rs);
        }
        addMemo.put(key, r);
        return r;
    }

    int sum(vector<int> gs) {
        Dy tot{0, 0};
        vector<int> rest;
        for (int g : gs) {
            if (N[g].isnum) tot = dadd(tot, N[g].v);
            else rest.push_back(g);
        }
        sort(rest.begin(), rest.end());
        int r = number(tot);
        for (int g : rest) r = add(r, g);
        return r;
    }
};

// ------------------------------------------------------------------ snort
struct Key3 {
    u64 c, l, r;
    bool operator==(const Key3& o) const { return c == o.c && l == o.l && r == o.r; }
};
struct Key3Hash {
    size_t operator()(const Key3& k) const {
        u64 h = k.c * 0x9e3779b97f4a7c15ULL ^ (k.l + 0x632be59bd9b4e019ULL) * 0xbf58476d1ce4e5b9ULL ^
                (k.r + 0x94d049bb133111ebULL) * 0xff51afd7ed558ccdULL;
        return Map64::h(h);
    }
};

struct Snort {
    Games& G;
    int n;
    vector<u64> adj;
    vector<vector<array<u64, 256>>> autos;  // per automorphism, per byte
    struct Entry { u64 c, l, r; int32_t v; };
    vector<Entry> tab;  // open addressing; c == 0 marks an empty slot
    size_t tmask = 0, tcount = 0;
    int memoGet(const Key3& k) const {
        size_t i = Key3Hash()(k) & tmask;
        while (tab[i].c) {
            if (tab[i].c == k.c && tab[i].l == k.l && tab[i].r == k.r) return tab[i].v;
            i = (i + 1) & tmask;
        }
        return -1;
    }
    void memoPut(const Key3& k, int v) {
        if ((tcount + 1) * 10 > tab.size() * 7) {
            vector<Entry> old;
            old.swap(tab);
            tab.assign(old.size() * 2, Entry{0, 0, 0, 0});
            tmask = tab.size() - 1;
            tcount = 0;
            for (auto& e : old) if (e.c) memoPut(Key3{e.c, e.l, e.r}, e.v);
        }
        size_t i = Key3Hash()(k) & tmask;
        while (tab[i].c) i = (i + 1) & tmask;
        tab[i] = Entry{k.c, k.l, k.r, v};
        tcount++;
    }
    // compact table for components with <= 32 vertices: key (c, pext(L,c) | pext(R,c) << |c|)
#pragma pack(push, 4)
    struct Entry2 { u64 c, code; int32_t v; };
#pragma pack(pop)
    vector<Entry2> tab2;
    size_t tmask2 = 0, tcount2 = 0;
    static inline u64 pext(u64 x, u64 m) {
#if defined(__BMI2__)
        return _pext_u64(x, m);
#else
        u64 r = 0; int k = 0;
        while (m) { u64 b = m & (~m + 1); if (x & b) r |= 1ULL << k; k++; m ^= b; }
        return r;
#endif
    }
    static inline size_t h2(u64 c, u64 code) { return Map64::h(c * 0x9e3779b97f4a7c15ULL ^ (code + 0x632be59bd9b4e019ULL)); }
    int memoGet2(u64 c, u64 code) const {
        size_t i = h2(c, code) & tmask2;
        while (tab2[i].c) {
            if (tab2[i].c == c && tab2[i].code == code) return tab2[i].v;
            i = (i + 1) & tmask2;
        }
        return -1;
    }
    void memoPut2(u64 c, u64 code, int v) {
        if ((tcount2 + 1) * 5 > tab2.size() * 4) {
            vector<Entry2> old;
            old.swap(tab2);
            tab2.assign(old.size() * 2, Entry2{0, 0, 0});
            tmask2 = tab2.size() - 1;
            tcount2 = 0;
            for (auto& e : old) if (e.c) memoPut2(e.c, e.code, e.v);
        }
        size_t i = h2(c, code) & tmask2;
        while (tab2[i].c) i = (i + 1) & tmask2;
        tab2[i] = Entry2{c, code, v};
        tcount2++;
    }
    long long computed = 0;
    chrono::steady_clock::time_point t0 = chrono::steady_clock::now(), last = t0;

    Snort(Games& g, int n_, vector<u64> adj_, const vector<vector<int>>& perms) : G(g), n(n_), adj(adj_) {
        int nb = (n + 7) / 8;
        for (auto& p : perms) {
            bool ident = true;
            for (int i = 0; i < n; i++) if (p[i] != i) ident = false;
            if (ident) continue;
            vector<array<u64, 256>> t(nb);
            for (int b = 0; b < nb; b++)
                for (int val = 0; val < 256; val++) {
                    u64 m = 0;
                    for (int k = 0; k < 8; k++)
                        if ((val >> k) & 1) {
                            int v = b * 8 + k;
                            if (v < n) m |= 1ULL << p[v];
                        }
                    t[b][val] = m;
                }
            autos.push_back(t);
        }
        tab.assign(1 << 16, Entry{0, 0, 0, 0});
        tmask = tab.size() - 1;
        tab2.assign(1 << 20, Entry2{0, 0, 0});
        tmask2 = tab2.size() - 1;
    }
    inline u64 mapmask(const vector<array<u64, 256>>& t, u64 m) const {
        u64 r = 0;
        for (size_t b = 0; b < t.size(); b++) { r |= t[b][m & 255]; m >>= 8; }
        return r;
    }

    void components(u64 alive, u64 Lt, u64 Rt, vector<u64>& out) {
        u64 rem = alive;
        while (rem) {
            u64 comp = rem & (~rem + 1), frontier = comp;
            while (frontier) {
                u64 nw = 0, f = frontier;
                while (f) {
                    u64 b = f & (~f + 1);
                    f ^= b;
                    u64 nb = adj[__builtin_ctzll(b)] & alive;
                    if (Lt & b) nb &= ~Lt;
                    else if (Rt & b) nb &= ~Rt;
                    nw |= nb;
                }
                nw &= ~comp;
                comp |= nw;
                frontier = nw;
            }
            out.push_back(comp);
            rem &= ~comp;
        }
    }

    int value(u64 alive, u64 Lt, u64 Rt) {
        u64 dead = Lt & Rt;
        alive &= ~dead; Lt &= alive; Rt &= alive;
        vector<u64> comps;
        components(alive, Lt, Rt, comps);
        vector<int> vals;
        for (u64 c : comps) vals.push_back(compValue(c, Lt & c, Rt & c));
        return G.sum(vals);
    }

    static inline bool keyLess(const Key3& a, const Key3& b) {
        if (a.c != b.c) return a.c < b.c;
        if (a.l != b.l) return a.l < b.l;
        return a.r < b.r;
    }

    int compValue(u64 c, u64 L, u64 R) {
        if ((c & (c - 1)) == 0) return L ? G.ONE : (R ? G.MONE : G.STAR);
        Key3 best{c, L, R};
        bool neg = false;
        Key3 sw{c, R, L};
        if (keyLess(sw, best)) { best = sw; neg = true; }
        for (auto& t : autos) {
            u64 mc = mapmask(t, c), ml = mapmask(t, L), mr = mapmask(t, R);
            Key3 k1{mc, ml, mr}, k2{mc, mr, ml};
            if (keyLess(k1, best)) { best = k1; neg = false; }
            if (keyLess(k2, best)) { best = k2; neg = true; }
        }
        int pc = __builtin_popcountll(best.c);
        int r;
        if (pc <= 32) {
            u64 code = pext(best.l, best.c) | (pext(best.r, best.c) << pc);
            r = memoGet2(best.c, code);
            if (r < 0) {
                r = compute(best.c, best.l, best.r);
                memoPut2(best.c, code, r);
            }
        } else {
            r = memoGet(best);
            if (r < 0) {
                r = compute(best.c, best.l, best.r);
                memoPut(best, r);
            }
        }
        return neg ? G.neg(r) : r;
    }

    int compute(u64 c, u64 L, u64 R) {
        computed++;
        if ((computed & 0xffff) == 0) {
            auto now = chrono::steady_clock::now();
            if (chrono::duration<double>(now - last).count() > 30) {
                last = now;
                fprintf(stderr, "[%.0fs] components %lld games %zu le %zu add %zu\n",
                        chrono::duration<double>(now - t0).count(), computed, G.N.size(), G.leMemo.cnt,
                        G.addMemo.cnt);
            }
        }
        vector<int> Ls, Rs;
        for (int side = 0; side < 2; side++) {
            bool left = side == 0;
            u64 movable = c & ~(left ? R : L);
            while (movable) {
                u64 b = movable & (~movable + 1);
                movable ^= b;
                int v = __builtin_ctzll(b);
                u64 na = c & ~b, nL, nR;
                if (left) { nL = (L | adj[v]) & na; nR = R & na; }
                else { nL = L & na; nR = (R | adj[v]) & na; }
                u64 dead = nL & nR;
                na &= ~dead;
                int val = value(na, nL & na, nR & na);
                (left ? Ls : Rs).push_back(val);
            }
        }
        return G.canon(Ls, Rs);
    }
};

int main() {
    int n, m;
    if (scanf("%d %d", &n, &m) != 2) return 1;
    vector<u64> adj(n, 0);
    for (int i = 0; i < m; i++) {
        int u, v;
        if (scanf("%d %d", &u, &v) != 2) return 1;
        adj[u] |= 1ULL << v;
        adj[v] |= 1ULL << u;
    }
    int k;
    if (scanf("%d", &k) != 1) return 1;
    vector<vector<int>> perms(k, vector<int>(n));
    for (auto& p : perms)
        for (int i = 0; i < n; i++)
            if (scanf("%d", &p[i]) != 1) return 1;
    int q;
    if (scanf("%d", &q) != 1) return 1;
    Games G;
    Snort S(G, n, adj, perms);
    vector<int> roots;
    for (int i = 0; i < q; i++) {
        unsigned long long a, l, r;
        if (scanf("%llu %llu %llu", &a, &l, &r) != 3) return 1;
        roots.push_back(S.value(a, l, r));
        fprintf(stderr, "position %d done: components %lld games %zu\n", i, S.computed, G.N.size());
    }
    // output reachable DAG, children first
    vector<char> seen(G.N.size(), 0);
    vector<int> order;
    function<void(int)> dfs = [&](int g) {
        // iterative to avoid deep recursion
        vector<pair<int, int>> st;
        st.push_back({g, 0});
        while (!st.empty()) {
            auto& [x, i] = st.back();
            if (i == 0 && seen[x]) { st.pop_back(); continue; }
            seen[x] = 1;
            int tot = G.N[x].nl + G.N[x].nr;
            if (i < tot) {
                int child = i < G.N[x].nl ? G.L(x)[i] : G.R(x)[i - G.N[x].nl];
                i++;
                if (!seen[child]) st.push_back({child, 0});
            } else {
                order.push_back(x);
                st.pop_back();
            }
        }
    };
    for (int r : roots) dfs(r);
    printf("ROOTS");
    for (int r : roots) printf(" %d", r);
    printf("\n");
    for (int g : order) {
        const Node& nd = G.N[g];
        if (nd.isnum) printf("N %d %lld %d\n", g, (long long)nd.v.n, nd.v.e);
        else {
            printf("G %d %d", g, nd.nl);
            for (int i = 0; i < nd.nl; i++) printf(" %d", G.L(g)[i]);
            printf(" %d", nd.nr);
            for (int i = 0; i < nd.nr; i++) printf(" %d", G.R(g)[i]);
            printf("\n");
        }
    }
    fprintf(stderr, "total components %lld, games %zu\n", S.computed, G.N.size());
    return 0;
}

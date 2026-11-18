# Snort on Apollonian networks

This repository computes the exact combinatorial-game value of **Snort** played on the
deterministic **Apollonian network** of each recursion depth, starting from the trivial
three-vertex case. It also explores the structure behind those values and proposes
conjectures for the general case.

![Apollonian networks A0–A3, vertices coloured by level](docs/apollonian.svg)

**Summary.**

| depth n | vertices | value of Snort on Aₙ | temperature | Δ (max degree) |
|---|---|---|---|---|
| 0 | 3 | ±2 | 2 | 2 |
| 1 | 4 | ±3 | 3 | 3 |
| 2 | 7 | ±6 | 6 | 6 |
| 3 | 16 | ±10 | 10 | 12 |
| 4 | 43 | ±(45/2±1/2) = {{23 \| 22} \| {−22 \| −23}} | 45/2 | 24 |

At every depth computed, Left's best first move is the **centre** d (the first inserted
vertex). Every other first move is dominated by it, so the value is the switch {Cₙ | −Cₙ},
where Cₙ is the position after Left colours d. Cₙ is an integer for n ≤ 3 (3, 6, 10) but
**not** at n = 4, where C₄ = {23 | 22}. Depth 4 is too large to search exhaustively; it was
settled by computing C₄ and two other first moves exactly and bounding the remaining 36 with
two Snort lemmas (Sections 2 and 8). Section 7 lists the conjectures.

---

## 1. Set-up

**Snort.** Left colours vertices blue and Right colours vertices red. A player may never
colour a vertex adjacent to a vertex of the *opponent's* colour. Under normal play, whoever
cannot move loses. A vertex adjacent to a blue vertex is *tinted* for Left: only Left can
still colour it. A vertex tinted for both players is dead. Values are canonical forms of
short partizan games (Conway, *On Numbers and Games*; Siegel, *Combinatorial Game
Theory*).

Notation: `±x` is the switch `{x | −x}`, `a±b` is `{a+b | a−b}`, `*` is star, and nested
braces are written out in full. Snort on an uncoloured graph is symmetric under swapping the
colours, so every value G below satisfies G = −G. Hence its mean is 0, G + G = 0, and the
game is either 0 or a first-player win.

**Apollonian networks.** `A0` is a triangle. `A(n+1)` is obtained from `An` by inserting a
new vertex into every inner triangular face created at the previous step and joining it to
that face's three corners. Vertex 3, inserted at depth 1, is the **centre**. A vertex
inserted at step *j* has *level* *j*; the outer corners have level 0.

| n | vertices 3+(3ⁿ−1)/2 | edges 3\|V\|−6 | centre degree 3·2ⁿ⁻¹ | corner degree 2ⁿ+1 | level-j degree 3·2ⁿ⁻ʲ | automorphisms |
|---|---|---|---|---|---|---|
| 0 | 3 | 3 | – | 2 | – | 6 |
| 1 | 4 | 6 | 3 | 3 | 3 | 24 |
| 2 | 7 | 15 | 6 | 5 | 6, 3 | 6 |
| 3 | 16 | 42 | 12 | 9 | 12, 6, 3 | 6 |
| 4 | 43 | 123 | 24 | 17 | 24, 12, 6, 3 | 6 |
| 5 | 124 | 366 | 48 | 33 | 48, …, 3 | 6 |

From depth 2 on, the centre is the unique vertex of maximum degree, Δ(Aₙ) = 3·2ⁿ⁻¹.

## 2. Values of Snort on Aₙ

| n | \|V\| | \|E\| | Δ | canonical value | temperature | Left / Right stop | outcome | canonical subpositions | birthday |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 3 | 3 | 2 | ±2 | 2 | 2 / −2 | 𝒩 | 6 | 3 |
| 1 | 4 | 6 | 3 | ±3 | 3 | 3 / −3 | 𝒩 | 8 | 4 |
| 2 | 7 | 15 | 6 | ±6 | 6 | 6 / −6 | 𝒩 | 14 | 7 |
| 3 | 16 | 42 | 12 | ±10 | 10 | 10 / −10 | 𝒩 | 22 | 11 |
| 4 | 43 | 123 | 24 | ±(45/2±1/2) | 45/2 | 22 / −22 | 𝒩 | 50 | 25 |

*Mean* is 0 throughout. 𝒩 means the first player wins. Depths 0–3 are exhaustive
computations (under a second). Depth 4 combines exact computation with two lemmas, as
explained below. Depth 5 (124 vertices) is out of reach.

Depths 0–2 are instances of a simple fact, also noted by Huntemann–Nowakowski–Santos: a
graph on m+1 vertices with a vertex u adjacent to all others has Snort value ±m. Proof: any
position P with k uncoloured vertices satisfies P ≤ k, by induction (every P^L has k−1
vertices, so P^L ≤ k−1 < k, and the integer k has no Right option). Colouring u leaves m
Left-tinted vertices, i.e. the integer m, and every other Left option is ≤ m, hence
dominated. A3 is the first case without such a vertex, and its value ±10 falls below Δ = 12.

### Left's first moves

Values of the position after Left colours one vertex, one row per orbit of the automorphism
group. Right's moves are the negatives. "≤ C" means the move is dominated by the centre move.

| n | vertex (level, degree) | value after Left's move | mean | temperature | ≤ C |
|---|---|---|---|---|---|
| 2 | corner (0, 5) | 7/2±3/2 | 7/2 | 3/2 | yes |
| 2 | **centre (1, 6)** | **6** | 6 | — (number) | — |
| 2 | level 2 (2, 3) | 3/2±7/2 | 3/2 | 7/2 | yes |
| 3 | corner (0, 9) | {23/2±3/2 \| 2} | 27/4 | 19/4 | yes |
| 3 | **centre (1, 12)** | **10** | 10 | — (number) | — |
| 3 | level 2 (2, 6) | {{13 \| 8±1} \| −2, ±4} | 17/4 | 25/4 | yes |
| 3 | level 3 (3, 3), next to the centre | {9 \| {−3 \| −17/2±1/2}} | 13/8 | 59/8 | yes |
| 3 | level 3 (3, 3), next to a corner | {{13 \| 8±1} \| {−13/2±1/2 \| −10}} | 9/8 | 75/8 | yes |
| 4 | corner (0, 17) | {{{39 \| {67/2±1/2 \| 30}} \| 45/2±1/2} \| 5} | 543/32 | 383/32 | yes |
| 4 | **centre (1, 24)** | **{23 \| 22} = 45/2±1/2** | 45/2 | 1/2 | — |
| 4 | level 2 (2, 12) | {{{{38 \| 67/2±1/2} \| 61/2±1/2} \| {{26 \| 45/2±1/2} \| 29/2±1/2}} \| −5, ±({27/2±1/2 \| 7})} | 85/8 | 125/8 | yes |
| 4 | level 3 (3, 6): 6 vertices next to the centre, 3 not | not computed | ≤ 45/2 | | yes, by Lemmas A–B |
| 4 | level 4 (4, 3): 12 next to the centre, 15 not | not computed | ≤ 45/2 | | yes, by Lemmas A–B |

At depth 3 the corner move K = {{13|10} | 2} has Left option {13|10}, which is *confused
with* 10 ({3|0} is a first-player win). K is nevertheless ≤ 10 and therefore dominated. So the
canonical form keeps a single Left option, and the value collapses to the pure switch ±10.

### How depth 4 was settled

The game tree of A₄ is too large to search exhaustively. The first move at a single degree-6
vertex alone generated more than 10⁸ new distinct components (10 GB of memo) before it was
stopped. Instead (`depth4.py`):

1. C₄ = {23 | 22} and the corner and level-2 first moves were computed exactly. The latter
   two are ≤ C₄.
2. For every first move v and every vertex u, Lemmas A and B (Section 8) give
   **P_v ≤ 1 + X_{v,u}**. Here P_v is the position after Left colours v, and X_{v,u} is the
   much smaller position after Left has coloured both v and u. For 33 of the remaining 36
   vertices, some "hub" u of level ≤ 2 already gives 1 + X_{v,u} ≤ C₄. For the 12 level-4
   neighbours of the centre this is an equality.
3. The last orbit is the 3 level-3 vertices v lying in a face with two corners and a level-2
   vertex. It is handled by the definition of ≤: P_v ≤ C₄ iff C₄'s Right option 22 is not
   ≤ P_v, and no Left option X_{v,w} of P_v is ≥ C₄.
   * Let u be the level-2 vertex adjacent to v. The first condition holds because
     mean(P_v) ≤ 1 + mean(X_{v,u}) = 47/4 < 22.
   * For the seven hubs w, X_{v,w} is compared with C₄ directly.
   * For the other 35 vertices w, mean(X_{v,w}) ≤ 1 + mean(X_{v,w,u}) ≤ 277/16, where X_{v,w,u}
     has v, w and u coloured by Left. This is below mean(C₄) = 45/2.

So every Left first move is ≤ C₄. The centre move is not reversible, since 22 ≰ A₄. Hence
**A₄ = {C₄ | −C₄} = ±(45/2±1/2)**, with temperature 45/2 and stops ±22. This relies on the
two lemmas, which are proved in Section 8 and also tested on random positions, together with
machine evaluation of the smaller positions.

## 3. Anatomy of the centre move

After Left colours the centre d, its Δ = 3·2ⁿ⁻¹ neighbours are Left-tinted. Every remaining
untinted vertex lies inside a triangle whose three corners are all Left-tinted. Each such
untinted region is the interior of a sub-network of depth n−2 (3 of them), n−3 (6 of them),
…, 1 (3·2ⁿ⁻³ of them), so 3(2ⁿ⁻²−1) *Left-cornered pockets* in all. Neighbouring pockets
share corners. The number of untinted vertices is 3·N(n−1), where N(0) = N(1) = 0 and
N(m) = (3ᵐ⁻¹−1)/2 + 2N(m−1). That gives 0, 0, 3, 18, 75 for n = 1, …, 5.

Edges between two Left-tinted vertices are irrelevant (Section 10), so tinted neighbours of d
with no untinted neighbour are isolated +1's. The rest forms one connected component Bₙ.

| n | Δ | isolated +1's | Bₙ: tinted + untinted vertices | value of Bₙ | Cₙ | Δ − mean(Cₙ) |
|---|---|---|---|---|---|---|
| 1 | 3 | 3 | – | – | 3 | 0 |
| 2 | 6 | 6 | – | – | 6 | 0 |
| 3 | 12 | 6 | 6 + 3 | 4 | 10 | 2 |
| 4 | 24 | 12 | 12 + 18 | {11 \| 10} | {23 \| 22} | 3/2 |

B₃ is a hexagon a–x–b–y–c–z (tinted corners a, b, c alternating with untinted x, y, z), with a
tinted pendant on each of x, y, z. Right's move at a pocket's centre kills all three of its
tinted corners at once, so in isolation a pocket costs Left about half of its corners. A lone
pocket T_k (Section 4) has mean 3/2, 3/2, 5/4 against 3 tinted corners. But pockets share
corners, and the total *deficit* Δ − mean(Cₙ) is only 2 at n = 3 (three pockets) and 3/2 at
n = 4 (nine pockets). So far it does not grow with the number of pockets.

## 4. Building blocks

Two families of sub-games recur inside these positions:

* **T_k**: the depth-k network with its three corners Left-tinted and its interior
  untinted (a lone pocket).
* **I_k(x, y, z)**: the interior of the depth-k network once its corners are *resolved*.
  Each corner is coloured by Left (L), by Right (R) or is dead (0). Once a separating triangle
  is resolved, its inside is an independent summand with exactly this value.

| block | k = 1 | k = 2 | k = 3 | k = 4 |
|---|---|---|---|---|
| T_k (pocket) | 3/2±3/2 | 3/2±9/2 | {10 \| −15/2±1/2} | not computed |
| I_k(0, 0, 0) (open interior) | * | ±3 | ±(15/2±1/2) | not computed |
| I_k(0, 0, L) | 1 | 5/2±1/2 | {21/2±1/2 \| 2} | {{31 \| 45/2±1/2} \| 5} |
| I_k(0, L, L) | 1 | 4 | {12 \| 17/2±1/2} | {67/2±1/2 \| 37/2±({6±1/2 \| 5/2})} |
| I_k(L, L, L) | 1 | 4 | 13 | **34±5** |
| I_k(L, L, R) | 0 | 1 | 4 | {12 \| 17/2±1/2} |
| I_k(0, L, R) | 0 | 0 | 0 | 0 |

The remaining cases follow by colour symmetry, e.g. I_k(L, R, R) = −I_k(L, L, R). Means and
temperatures at k = 4: I₄(0,0,L) has m = 127/8, t = 87/8; I₄(0,L,L) has m = 26, t = 15/2;
I₄(L,L,L) has m = 34, t = 5; I₄(L,L,R) has m = 41/4, t = 7/4. T₄ and I₄(0,0,0) are as large
as A₄ itself and were not computed.

Observations:

* **I_k(0, L, R) = 0 for every k (theorem).** Reflect in the axis through the dead corner.
  The fixed vertices are exactly the centres on that axis, and each is adjacent to both
  coloured corners, so all are dead. No edge joins a vertex to its mirror image, and the
  reflection swaps L-tints with R-tints. The second player therefore wins by answering a move
  at v with the opposite colour at its mirror image.
* **Mixed corners split (theorem).** If the corners carry both colours, the centre of the
  triangle is adjacent to both and dies. Its inside then falls apart into three independent
  sub-interiors, so I_k(L, L, R) = I_{k−1}(0, L, L) + 2·I_{k−1}(0, L, R) = I_{k−1}(0, L, L).
  So the essential blocks are T_k, I_k(0,0,0), I_k(0,0,L), I_k(0,L,L) and I_k(L,L,L).
* **Fully Left-cornered interiors are not always integers.** For k ≤ 3 every interior
  vertex touches a corner, so I_k(L, L, L) is trivially (3ᵏ−1)/2. At k = 4 there are 6
  untinted interior vertices, and I₄(L, L, L) = 34±5 = {39 | 29}. Left cannot secure all 40
  vertices even moving first, and Right moving first holds Left to 29.
* **Means track tints.** In every block above, the mean is within 2 of (number of
  Left-tinted vertices) − (number of Right-tinted vertices): untinted regions are worth
  about 0 on average. At k = 4: I(L,L,L) has 34 tinted vertices and mean 34; I(0,L,L) has 26
  and mean 26; I(0,0,L) has 15 and mean 127/8. Pockets T_k have 3 and mean 3/2, 3/2, 5/4.
  The centre-move positions Cₙ have Δ and mean Δ, Δ, Δ−2, Δ−3/2.
* The *open* interior I_k(0, 0, 0) (Aₖ minus its outer triangle) is *, ±3, ±(15/2±1/2) for
  k = 1, 2, 3.

## 5. Context: all planar 3-trees

Aₙ is the most symmetric member of the class of **planar 3-trees**: triangulations built
from a triangle by repeatedly stacking a vertex into *any* face, also called Apollonian
networks in the broad sense. To see which features are special to Aₙ, every planar 3-tree
with at most 14 vertices was evaluated: 72,390 graphs up to isomorphism. The class counts
1, 1, 1, 1, 3, 7, 24, 93, 434, 2110, 11002, 58713 for 3, …, 14 vertices agree with OEIS
A027610. So were 860 random ones with up to 32 vertices.

**All planar 3-trees** (exhaustive, up to isomorphism):

| \|V\| | graphs | pure switch ±x | t = Δ | max (t − Δ) | min t/Δ | mean t/Δ | first-player win |
|---|---|---|---|---|---|---|---|
| 3 | 1 | 1 | 1 | 0 | 1.000 | 1.000 | 1 |
| 4 | 1 | 1 | 1 | 0 | 1.000 | 1.000 | 1 |
| 5 | 1 | 1 | 1 | 0 | 1.000 | 1.000 | 1 |
| 6 | 1 | 1 | 1 | 0 | 1.000 | 1.000 | 1 |
| 7 | 3 | 3 | 3 | 0 | 1.000 | 1.000 | 3 |
| 8 | 7 | 4 | 4 | 0 | 0.750 | 0.893 | 7 |
| 9 | 24 | 12 | 12 | 0 | 0.750 | 0.891 | 24 |
| 10 | 93 | 27 | 27 | 0 | 0.643 | 0.859 | 93 |
| 11 | 434 | 82 | 82 | 0 | 0.500 | 0.845 | 434 |
| 12 | 2110 | 249 | 228 | 0 | 0.333 | 0.836 | 2110 |
| 13 | 11002 | 1039 | 733 | 0 | 0.429 | 0.826 | 11002 |
| 14 | 58713 | 4499 | 2290 | 0 | 0.286 | 0.820 | 58713 |

**Random planar 3-trees** (each new vertex stacked into a uniformly random face):

| \|V\| | graphs | pure switch ±x | t = Δ | max (t − Δ) | min t/Δ | mean t/Δ | first-player win |
|---|---|---|---|---|---|---|---|
| 4 | 40 | 40 | 40 | 0 | 1.000 | 1.000 | 40 |
| 5 | 40 | 40 | 40 | 0 | 1.000 | 1.000 | 40 |
| 6 | 40 | 40 | 40 | 0 | 1.000 | 1.000 | 40 |
| 7 | 40 | 40 | 40 | 0 | 1.000 | 1.000 | 40 |
| 8 | 40 | 25 | 25 | 0 | 0.750 | 0.906 | 40 |
| 9 | 40 | 23 | 23 | 0 | 0.750 | 0.907 | 40 |
| 10 | 40 | 9 | 9 | 0 | 0.786 | 0.849 | 40 |
| 11 | 40 | 4 | 4 | 0 | 0.607 | 0.830 | 40 |
| 12 | 40 | 5 | 5 | 0 | 0.667 | 0.848 | 40 |
| 13 | 40 | 7 | 3 | 0 | 0.667 | 0.834 | 40 |
| 14 | 40 | 2 | 1 | 0 | 0.611 | 0.834 | 40 |
| 15 | 40 | 1 | 0 | -1 | 0.694 | 0.805 | 40 |
| 16 | 40 | 0 | 0 | -1/2 | 0.600 | 0.820 | 40 |
| 17 | 40 | 0 | 0 | -3/4 | 0.659 | 0.796 | 40 |
| 18 | 40 | 0 | 0 | -1 | 0.659 | 0.819 | 40 |
| 19 | 25 | 1 | 0 | -9/8 | 0.688 | 0.809 | 25 |
| 20 | 25 | 0 | 0 | -5/4 | 0.625 | 0.808 | 25 |
| 21 | 25 | 0 | 0 | -1/4 | 0.696 | 0.837 | 25 |
| 22 | 25 | 0 | 0 | -9/8 | 0.679 | 0.815 | 25 |
| 23 | 25 | 1 | 1 | 0 | 0.641 | 0.810 | 25 |
| 24 | 25 | 0 | 0 | -3/4 | 0.673 | 0.835 | 25 |
| 25 | 25 | 0 | 0 | -5/4 | 0.661 | 0.811 | 25 |
| 26 | 25 | 0 | 0 | -9/8 | 0.620 | 0.787 | 25 |
| 27 | 10 | 0 | 0 | -15/8 | 0.712 | 0.805 | 10 |
| 28 | 10 | 0 | 0 | -3/2 | 0.691 | 0.820 | 10 |
| 29 | 10 | 0 | 0 | -11/8 | 0.759 | 0.838 | 10 |
| 30 | 10 | 0 | 0 | -9/4 | 0.738 | 0.788 | 10 |
| 31 | 10 | 0 | 0 | -7/8 | 0.788 | 0.857 | 10 |
| 32 | 10 | 0 | 0 | -1/2 | 0.667 | 0.820 | 10 |

Findings:

* **Every** planar 3-tree in both samples is hot (a first-player win), and **every** one
  satisfies t ≤ Δ.
* Up to 13 vertices, **t = Δ holds exactly when the graph has a vertex adjacent to all
  others** (then the value is ±Δ). The counts with t = Δ, namely 4, 12, 27, 82, 228, 733 for
  8, …, 13 vertices, are exactly the numbers of triangulated polygons up to symmetry
  (OEIS A000207), i.e. of planar 3-trees with a universal vertex. **At 14 vertices this
  breaks:** besides the 2,282 graphs with a universal vertex, 8 graphs with Δ = 8 have
  t = 8. Their best move is not a number but a hot option with mean exactly Δ, e.g.
  ±({12 | 4, 4±2}). Their edge lists are in `data/planar3trees_14.jsonl`.
* Pure switches ±x without a universal vertex are rare: 21 graphs on 12 vertices are ±6 with
  Δ = 9, 306 on 13 vertices are ±7, and 2,217 on 14 vertices are ±8 (Δ = 10 or 11).
  A₃ = ±10 (Δ = 12) belongs to this group.
* The temperature of a planar 3-tree can be much smaller than Δ. The coldest case on 12
  vertices has t = 2, Δ = 6. Such cases are path-like stackings: for the cube of a path
  Pₘ³ (vertex i joined to i±1, i±2, i±3, the "linear" planar 3-tree) the temperature stays
  between 2 and 6 for all m ≤ 40. In contrast, t(Aₙ) roughly doubles with each level.

## 6. Variant: subdividing both faces of the triangle

If the initial triangle is viewed on the sphere and *both* of its faces are refined, the
depth-1 graph is the triangular bipyramid. The values become more intricate, and the best
first move is now an outer corner (degree 2ⁿ⁺¹):

| n | \|V\| | Δ | value | temperature | stops |
|---|---|---|---|---|---|
| 0 | 3 | 2 | ±2 | 2 | 2 / −2 |
| 1 | 5 | 4 | ±4 | 4 | 4 / −4 |
| 2 | 11 | 8 | ±({9 \| 9/2±1/2}) | 27/4 | 5 / −5 |
| 3 | 29 | 16 | ±({{26 \| {41/2±1/2 \| 17}} \| {25/2±1/2 \| 4}}) | 245/16 | 12 / −12 |

Here too t ≤ Δ, with t/Δ = 1, 1, 0.84, 0.96.

## 7. Conjectures

Let d be the centre of Aₙ and Cₙ the position after Left colours it.

1. **(Shape of the value.) The centre is the only good first move.** For every n ≥ 2,
   every first move other than at d is strictly dominated by the move at d, so
   **Aₙ = {Cₙ | −Cₙ} = ±Cₙ**. *(True for 2 ≤ n ≤ 4. For every n it holds for the 3ⁿ⁻¹
   level-n vertices, about two thirds of the board; see Section 9.)* This concerns
   domination, not which moves win: the corner move also wins for n = 2, 3, 4.
2. **(Cₙ is nearly cold.)** Cₙ has temperature at most 1/2. It is an integer for n ≤ 3
   (3, 6, 10) and C₄ = {23 | 22}. Consequently Aₙ is, up to a tiny tepid part, the switch
   ±mₙ with mₙ = mean(Cₙ). Its stops are ±(right stop of Cₙ) and its temperature is
   **t(Aₙ) = mean(Cₙ)**. *(True for n ≤ 4. The weaker statement Cₙ > 0, i.e. the centre
   move wins, is proved for n ≤ 7 in Section 9.)*
3. **(Temperature is governed by the centre's degree.)**
   t(Aₙ) ≤ Δ(Aₙ) (= 3·2ⁿ⁻¹ for n ≥ 1), with equality iff n ≤ 2. The deficit Δ − t(Aₙ) = 0, 0, 0, 2, 3/2
   stays bounded: **t(Aₙ) = 3·2ⁿ⁻¹ − O(1)**. In terms of size, t(Aₙ) grows like
   |V|^(log 2 / log 3) ≈ |V|^0.63. That is strictly between the bounded temperatures of
   path-like planar 3-trees and the linear growth of stars and complete graphs.
   *(Weakest of the conjectures. The supporting evidence is the two values 2 and 3/2, the
   pocket-sharing mechanism of Section 3, and Conjecture 5. A safer version is
   t(Aₙ) = Θ(2ⁿ), i.e. εΔ ≤ t(Aₙ) ≤ Δ for some ε > 0. At depth 5, Δ = 48.)*
4. **(Planar 3-trees obey the degree bound.)** For every planar 3-tree G, Snort on G is hot
   (a first-player win) and **t(G) ≤ Δ(G)**. This is the "temperature ≤ degree" conjecture
   of Huntemann–Nowakowski–Santos (2019) restricted to planar 3-trees. That conjecture is
   false for general graphs: Huntemann and Maciosowski (2024) give caterpillars with
   t = 2Δ − 3. *(Verified exhaustively for |V| ≤ 14 (72,390 graphs) and on 860
   random examples with |V| ≤ 32.)* Equality holds whenever G has a universal vertex. The
   converse holds up to 13 vertices but fails at 14 (Section 5), so it is not part of the
   conjecture.
5. **(Means are tint counts up to O(1).)** For the positions arising in Aₙ (pockets,
   resolved interiors, Cₙ), |mean − (#Left-tinted − #Right-tinted)| stays bounded
   independently of the depth. All computed cases are within 2. Conjecture 3 is the special
   case Cₙ. This fails for general graphs: a Left-tinted vertex with many untinted leaves is
   worth far more than 1. So the claim is specific to these triangulated pockets.
6. **(Open interiors.)** The open interior I_k(0, 0, 0) is a symmetric switch whose
   temperature grows like 2ᵏ (0, 3, 15/2 for k = 1, 2, 3).

*Refuted along the way.* From k ≤ 3 it was tempting to conjecture that a triangle with all
three corners coloured has an integer inside (I_k(L,L,L) = (3ᵏ−1)/2,
I_k(L,L,R) = (3ᵏ⁻¹−1)/2). k = 4 refutes both: I₄(L,L,L) = 34±5 and
I₄(L,L,R) = {12 | 17/2±1/2}.

## 8. Two Snort lemmas (used at depth 4)

Write a position as (alive vertices, Left-tinted set, Right-tinted set).

**Lemma A (Left tints never hurt Left).** If Q′ is obtained from Q by adding Left tints and
deleting Right-tinted vertices, then Q ≤ Q′.

*Proof.* Show Q′ − Q ≥ 0, i.e. Left wins Q′ + (−Q) moving second. In −Q, a Right move is a
blue colouring in Q and a Left move is a red colouring in Q. Left copies every move on the
other board:
* Right colours w red in Q′: Left colours w red in Q, which is legal because L(Q) ⊆ L(Q′).
* Right colours x blue in Q: Left colours x blue in Q′, which is legal because Q and Q′
  have the same Right tints on common vertices, and every vertex missing from Q′ is
  Right-tinted in Q.

After each exchange the relation "Q′ = Q plus Left tints minus Right-tinted vertices" still
holds. A vertex that dies only in Q′ is Right-tinted in Q, so Left always has a reply. ∎

**Lemma B (a Left-tinted vertex is worth at most 1 plus its tinting).** If u is Left-tinted
in Q, then Q ≤ 1 + Q^{L@u}, where Q^{L@u} is the position after Left colours u.

*Proof.* Same copying strategy between Q^{L@u} and Q. Every neighbour of u is Left-tinted in
Q^{L@u}, so Right can never colour one there, and u therefore stays alive and Left-tinted in
Q. When Right colours u blue in Q, Left answers by moving in the integer 1. After that the
two boards satisfy the relation of Lemma A, and Left keeps copying. ∎

Both lemmas are also checked on hundreds of random positions in `tests/test_engine.py`.

**Corollary.** For any first move v and any other vertex u, let P_v⁺ be P_v with u
additionally Left-tinted. Then P_v ≤ P_v⁺ ≤ 1 + X_{v,u}. The first step is Lemma A and the
second is Lemma B. Hence:
* if 1 + X_{v,u} ≤ C₄, the move at v is dominated by the centre move;
* mean(P_v) ≤ 1 + mean(X_{v,u}).

For a level-n vertex v adjacent to the centre d, N(v) ⊆ N[d], and the bound is exact:
P_d = 1 + X_{v,d}.

## 9. Toward Conjecture 1 for all depths

Conjecture 1 has two directions (for n ≥ 2; at n = 1 all four vertices of K₄ are equivalent):

* **(D1) the centre move is best:** P_v ≤ Cₙ for every first move v;
* **(D2) only the centre move is best:** P_v ≱ Cₙ for every v ≠ d. Together with D1, this
  says P_v < Cₙ.

These are statements about *domination*, not about which first moves *win*. A first move v
wins when P_v ≥ 0, so that the opponent, moving next, loses. In that sense the centre is not
the only good move: the corner move also wins at n = 2, 3, 4 (7/2±3/2, {23/2±3/2 | 2} and
{{{39 | {67/2±1/2 | 30}} | 45/2±1/2} | 5} are all > 0). So "a first move wins iff it is
the centre move" is false. Its "if" half, that the centre move wins, is Theorem C2 below.

**Status.** Both directions hold for 2 ≤ n ≤ 4:
* n ≤ 3 by the exact values.
* n = 4 by Section 2 plus strictness. The corner and level-2 moves are known exactly and
  differ from C₄. The level-3 moves have mean ≤ 47/4 or ≤ 91/8, below mean(C₄) = 45/2.
  The level-4 moves are strictly dominated by Theorem C1 below.

For general n, both directions are proved for the level-n vertices, and the rest remains
open.

**Lemma A′.** Deleting a Left-tinted vertex never helps Left: Q ≥ Q − u. *(Copying
strategy: the two boards stay identical apart from u, which Left never needs.)*

**Theorem C1 (closed-neighbourhood domination, any graph).** If N[v] ⊆ N[x], then
P_v ≤ P_x. If moreover x has a neighbour w outside N[v], then P_v < P_x.

*Proof.* Let X be the position after Left has coloured both v and x.
* In P_x, v is Left-tinted and every other neighbour of v lies in N(x), so v is an isolated
  +1 and P_x = 1 + X.
* In P_v, x is Left-tinted, so P_v ≤ 1 + X by Lemma B.
* For strictness, Left moving first wins 1 + X − P_v. In −P_v she makes the move that
  corresponds to Right colouring w in P_v, which kills x. Call the result Y = P_v^{R@w}.
  Adding Left tints on N(x) can only raise Y (Lemma A). The result is X with the
  Left-tinted vertex w and some Left-tinted neighbours of w deleted, and Right tints added
  on the rest of N(w). Both changes can only lower X (Lemma A′ and the colour mirror of
  Lemma A). So Y ≤ X, and 1 + X − Y ≥ 1 > 0. ∎

**Corollary (every n ≥ 2).** Each of the 3ⁿ⁻¹ level-n vertices v has degree 3 and lies in a
face (x, y, z) with N[v] = {v, x, y, z} ⊆ N[x], and x has further neighbours. So the move
at v is strictly worse than the move at each of x, y and z. Hence:
* *(D2 for level n.)* No level-n first move is ever optimal; none survives in the canonical
  form.
* *(D1 and D2 for the centre's degree-3 neighbours.)* P_v < Cₙ for the 3·2ⁿ⁻² level-n
  neighbours of d.
* Both directions of Conjecture 1 reduce to the vertices of level ≤ n−1, which form a copy of
  the vertex set of Aₙ₋₁. Level-n vertices make up about two thirds of Aₙ.

`conjecture1.py` checks the neighbourhood conditions for n ≤ 7, and the test suite checks
Theorem C1 on random graphs.

The local argument stops here. A level-(n−1) vertex has exactly one neighbour outside N[x]
for each face corner x. In random graphs, "exactly one private neighbour" fails to give
domination in about half of all such pairs (1,341 of 2,754 tested). What remains, e.g.
corner versus centre, is a global comparison: the two moves tint overlapping but
different hubs, and Right can attack each through different pockets.

**Theorem C2 (the centre move wins).** Cₙ > 0 for 1 ≤ n ≤ 7.

*Proof.* For n ≤ 2, Cₙ = 3 or 6. For n ≥ 3, the 3·2ⁿ⁻² level-n neighbours of d have all
their neighbours in N[d], so they are isolated +1's: Cₙ = k + Bₙ with k = 3·2ⁿ⁻².
Deleting every Left-tinted vertex of Bₙ can only lower it (Lemma A′). What remains are the
pockets of Section 3: 3·2ⁿ⁻²⁻ʲ untinted copies of the open interior I_j(0,0,0), for
j = 1, …, n−2. Snort on an uncoloured graph satisfies G = −G, so G + G = 0, and the pockets
sum to I_{n−2}(0,0,0); only the depth-(n−2) count, 3, is odd. Hence

  Cₙ ≥ k + I_{n−2}(0,0,0).

Any position satisfies Q ≥ −(number of uncoloured vertices that are not Left-tinted), by
induction: each Right move removes one. So Cₙ ≥ 3·2ⁿ⁻² − (3ⁿ⁻²−1)/2, which is 5, 8, 11, 8
for n = 3, …, 6. For n = 7 this bound is −25, so a sharper one is needed. Lemmas A and B at
the centre of I₅ give I₅ ≤ 1 + 3·I₄(0,0,L), and I₅ = −I₅, so C₇ ≥ 95 − 3·I₄(0,0,L). The
Left stop of 3·I₄(0,0,L) is 58 < 95, so C₇ > 0. ∎

For general n, the same argument gives Cₙ > 0 as soon as the Left stop of the open interior
I_{n−2}(0,0,0) is below 3·2ⁿ⁻², half the centre's degree. Conjecture 3 predicts about a
quarter. A bound of this kind for all n is the missing ingredient. The recursive estimate
used at n = 7 does not suffice beyond it, because Lemma B gives Left whole hubs for free.

## 10. Method and verification

* `cgt.py`: a self-contained canonical-form engine for short partizan games. It covers
  hash-consed canonical forms, removal of dominated options and bypassing of reversible ones,
  sums with number translation, comparison, dyadic numbers, and thermographs (temperature,
  mean and stops).
* `snort.py`: Snort positions as bitmasks (alive, Left-tinted, Right-tinted). Two exact
  reductions are applied. Edges between two equally tinted vertices are deleted (colouring
  one end only re-tints the other with the tint it already has). Positions are then split
  into connected components and their values summed. Components are memoised up to the
  automorphisms of the host graph and up to colour swap (which negates the value).
* `csrc/snort.cpp`: the same algorithm in C++ for speed, with compact hash tables (about
  80 bytes per memoised component). `snortc.py` imports its output into `cgt.py`. By
  default it re-canonicalises every node, so the Python engine re-checks the C++ result.
  The exact depth-4 computations explore about 2·10⁷ components (the level-2 first move).
* `tests/test_engine.py` checks the engine against independent brute force:
  * outcome classes of hundreds of random Snort positions against plain minimax;
  * outcomes of disjoint unions against the sum of the canonical values;
  * every claimed equality G = H, by brute-force search on Snort(G) + (−H), which must be a
    second-player win;
  * values with and without component decomposition, known values (Kₙ = ±(n−1), stars
    K₁,ₙ = ±n), thermographs, the C++ back end against the Python reference, and the
    planar-3-tree counts;
  * Lemmas A, A′ and B and Theorem C1 (Sections 8–9) on hundreds of random positions.

```
python3 tests/test_engine.py           # all checks (about a minute)
python3 explore.py 3                   # Sections 2 table, depths 0–3 (seconds)
python3 depth4.py --exact              # depth 4 (about 1–2 h, ~4 GB RAM)
python3 conjecture1.py                 # Section 9 (about a minute)
python3 explore.py 3 --both-faces      # Section 6
python3 blocks.py 4                    # Section 4
python3 enumerate_3trees.py 13 > data/planar3trees.jsonl   # n = 14 adds ~1 h; stored compactly
python3 random_apollonian.py 4 18 40 1 > data/random_apollonian.jsonl
python3 random_apollonian.py 19 26 25 2 > data/random_apollonian_large.jsonl
python3 random_apollonian.py 27 32 10 3 > data/random_apollonian_xl.jsonl
python3 summarize.py                   # Section 5 tables
python3 figure.py > docs/apollonian.svg
```

Raw results are in `data/`.

## References

* E. Berlekamp, J. Conway, R. Guy, *Winning Ways for your Mathematical Plays* (Snort is
  due to Simon Norton).
* A. N. Siegel, *Combinatorial Game Theory*, AMS Graduate Studies in Mathematics 146 (2013).
* S. Huntemann, R. J. Nowakowski, C. P. dos Santos, *Bounding game temperature using
  confusion intervals*, Theoret. Comput. Sci. 855 (2021) 43–60,
  [arXiv:1908.08471](https://arxiv.org/abs/1908.08471). Graphs with a universal vertex;
  the conjecture t ≤ degree.
* S. Huntemann, T. Maciosowski, *Degrees are useless in Snort when measuring temperature*
  (2024), [arXiv:2406.02107](https://arxiv.org/abs/2406.02107). Counterexamples to
  t ≤ degree and stars K₁,ₙ = ±n.
* J. S. Andrade Jr., H. J. Herrmann, R. F. S. Andrade, L. R. da Silva, *Apollonian
  networks*, Phys. Rev. Lett. 94 (2005) 018702.
* OEIS [A027610](https://oeis.org/A027610) (planar 3-trees) and
  [A000207](https://oeis.org/A000207) (triangulations of a polygon up to symmetry).

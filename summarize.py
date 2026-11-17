"""
Summaries (Markdown) of the planar-3-tree survey and the random sample.

usage: python3 summarize.py
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from fractions import Fraction as F


def load(path):
    if not os.path.exists(path):
        return []
    return [json.loads(line) for line in open(path)]


def table(rows, title):
    by = defaultdict(list)
    for r in rows:
        by[r["n"]].append(r)
    print(f"\n{title}\n")
    print("| \\|V\\| | graphs | pure switch ±x | t = Δ | max (t − Δ) | min t/Δ | mean t/Δ | first-player win |")
    print("|---|---|---|---|---|---|---|---|")
    for n in sorted(by):
        rs = by[n]
        ts = [F(r["temperature"]) for r in rs]
        d = [t - r["max_degree"] for t, r in zip(ts, rs)]
        ratio = [t / r["max_degree"] for t, r in zip(ts, rs)]
        print(f"| {n} | {len(rs)} | {sum(r['pure_switch'] for r in rs)} | {sum(x == 0 for x in d)} | "
              f"{max(d)} | {float(min(ratio)):.3f} | {float(sum(ratio) / len(ratio)):.3f} | "
              f"{sum(t > 0 for t in ts)} |")


def main():
    table(load("data/planar3trees.jsonl"), "All planar 3-trees (exhaustive, up to isomorphism)")
    table(load("data/random_apollonian.jsonl") + load("data/random_apollonian_large.jsonl"),
          "Random Apollonian networks (uniform random face at each step)")


if __name__ == "__main__":
    main()

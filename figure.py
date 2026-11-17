"""
Draw the Apollonian networks A_0..A_3 as an SVG (no dependencies).
Each inserted vertex is placed at the centroid of its face; colour = level.

usage: python3 figure.py > docs/apollonian.svg
"""

from apollonian import apollonian

COLOURS = ["#222222", "#d1495b", "#edae49", "#00798c", "#30638e"]


def positions(depth):
    g, info = apollonian(depth)
    pos = {0: (0.0, 1.0), 1: (-0.866, -0.5), 2: (0.866, -0.5)}
    faces = [(0, 1, 2)]
    v = 3
    for _ in range(depth):
        new = []
        for a, b, c in faces:
            pos[v] = tuple((pos[a][i] + pos[b][i] + pos[c][i]) / 3 for i in range(2))
            new += [(a, b, v), (b, c, v), (a, c, v)]
            v += 1
        faces = new
    return g, info, pos


def main():
    W, H, pad, R = 220, 210, 15, 90
    parts = []
    for k in range(4):
        g, info, pos = positions(k)
        ox = pad + k * W + W / 2
        oy = pad + 115

        def xy(p):
            return ox + R * p[0], oy - R * p[1]

        for u, w in g.edges:
            (x1, y1), (x2, y2) = xy(pos[u]), xy(pos[w])
            parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                         f'stroke="#888" stroke-width="0.8"/>')
        for v in range(g.n):
            x, y = xy(pos[v])
            r = 5.5 if info["level"][v] == 0 else max(2.5, 5.0 - 0.8 * info["level"][v])
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{COLOURS[info["level"][v]]}"/>')
        parts.append(f'<text x="{ox:.0f}" y="{oy + 85:.0f}" text-anchor="middle" font-family="sans-serif" '
                     f'font-size="13">A{k}: {g.n} vertices</text>')
    width = 2 * pad + 4 * W
    height = 2 * pad + H
    print(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
          f'viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="white"/>')
    print("\n".join(parts))
    print("</svg>")


if __name__ == "__main__":
    main()

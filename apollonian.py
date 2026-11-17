"""
Deterministic Apollonian networks.

Depth 0 is a triangle.  Depth k+1 is obtained from depth k by inserting a new
vertex into every *inner* triangular face created at depth k (i.e. every face
of the current subdivision of the original triangle) and joining it to the
three corners of that face.

    depth   vertices            edges
      k     3 + (3^k - 1)/2     3|V| - 6   (k >= 1; the triangle has 3)

Vertex labels: 0, 1, 2 are the outer corners, 3 is the first inserted vertex
(the "centre"), and the vertices of depth j are labelled consecutively after
those of depth j-1.
"""

from __future__ import annotations

from snort import Graph


def apollonian(depth: int, outer_face=False):
    """Return (Graph, info) for the depth-`depth` Apollonian network.

    If outer_face is True the outer face is subdivided too (the "tetrahedral"
    variant obtained by starting from K4 and filling all four faces).
    """
    edges = {(0, 1), (1, 2), (0, 2)}
    faces = [(0, 1, 2)]
    if outer_face:
        faces = [(0, 1, 2), (0, 1, 2)]
    n = 3
    level = [0, 0, 0]
    for d in range(1, depth + 1):
        new_faces = []
        for (a, b, c) in faces:
            v = n
            n += 1
            level.append(d)
            edges |= {(a, v), (b, v), (c, v)}
            new_faces += [(a, b, v), (b, c, v), (a, c, v)]
        faces = new_faces
    g = Graph(n, edges)
    return g, {"level": level, "faces": faces}


def n_vertices(depth: int) -> int:
    return 3 + (3 ** depth - 1) // 2

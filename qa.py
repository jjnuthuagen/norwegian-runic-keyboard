#!/usr/bin/env python3
"""Checks that catch the faults this typeface keeps producing.

Every one of these started as something spotted by eye and then measured.
Run it after any change to the geometry: `python3 qa.py`.
"""

import math
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import runefont as rf
import runes

ORDER = "abcdefghijklmnopqrstuvwxyzæøå"


def centrelines(els):
    out = []
    for e in els:
        k = e[0]
        if k in ("O", "D"):
            continue
        if k == "S":
            pts = [(0, 0), (0, rf.CAP)]
        elif k == "V":
            pts = [(e[1], e[2]), (e[1], e[3])]
        elif k == "L":
            pts = [(e[1], e[2]), (e[3], e[4])]
        elif k == "P":
            pts = rf._expand(e[1], rf.CURVE)
        elif k == "A":
            pts = rf._quad(*e[1])
        else:
            continue
        closed = math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < 1e-6
        f = (rf._fillet_closed(rf._dedupe(pts)[:-1], rf.RADIUS) if closed
             else rf._fillet(rf._dedupe(pts), rf.RADIUS))
        out.append(rf._dedupe(f))
    return out


def _seg_hit(a, b, c, d):
    def side(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    d1, d2 = side(c, d, a), side(c, d, b)
    d3, d4 = side(a, b, c), side(a, b, d)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def _crosses(p, q):
    for i in range(len(p) - 1):
        for j in range(len(q) - 1):
            if _seg_hit(p[i], p[i + 1], q[j], q[j + 1]):
                return True
    return False


def _sample(poly, step=6):
    pts = []
    for i in range(len(poly) - 1):
        a, b = poly[i], poly[i + 1]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        for j in range(max(1, int(L / step))):
            t = j / max(1, int(L / step))
            pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    pts.append(poly[-1])
    return pts


def merges():
    """Two strokes closer than the stroke width fuse into one thick line.

    Strokes are meant to touch where one ENDS on another -- a branch on
    the stave, a crossbar on a leg, an arch springing from a leg. Those
    T-junctions are excluded; what is left is two strokes that were meant
    to run apart and do not."""
    bad = []
    half = rf.WEIGHT / 2
    for c in ORDER:
        has_stave = any(e[0] == "S" for e in rf.GLYPHS[c])
        cls = [_sample(p) for p in centrelines(rf.GLYPHS[c])]
        for i in range(len(cls)):
            for j in range(i + 1, len(cls)):
                # a T-junction: either stroke's endpoint sits on the other
                def on(pt, poly):
                    return any(math.hypot(pt[0] - q[0], pt[1] - q[1]) <= half + 2
                               for q in poly)
                ends_i = (cls[i][0], cls[i][-1])
                ends_j = (cls[j][0], cls[j][-1])
                if any(on(e, cls[j]) for e in ends_i) or \
                   any(on(e, cls[i]) for e in ends_j):
                    continue
                # strokes that genuinely cross are meant to (h, m, x)
                if _crosses(cls[i], cls[j]):
                    continue
                best, at = 1e9, None
                for p in cls[i]:
                    for q in cls[j]:
                        # proximity buried inside the stave's own ink is
                        # invisible -- two arms meeting the stave from
                        # opposite sides are not a merge
                        if has_stave and abs(p[0]) <= half + 2 and abs(q[0]) <= half + 2:
                            continue
                        d = math.hypot(p[0] - q[0], p[1] - q[1])
                        if d < best:
                            best, at = d, p
                if at is not None and best < rf.WEIGHT:
                    bad.append((c, i, j, round(best), round(rf.WEIGHT - best),
                                (round(at[0]), round(at[1]))))
    return bad


def dot_clearance():
    out = []
    for c in ORDER:
        strokes = centrelines(rf.GLYPHS[c])
        for e in rf.GLYPHS[c]:
            if e[0] != "O":          # a disc IS the letterform in c
                continue
            _, cx, cy, r = e
            best = 1e9
            for s in strokes:
                for i in range(len(s) - 1):
                    ax, ay, bx, by = s[i][0], s[i][1], s[i + 1][0], s[i + 1][1]
                    dx, dy = bx - ax, by - ay
                    t = max(0, min(1, ((cx - ax) * dx + (cy - ay) * dy) / (dx * dx + dy * dy or 1e-9)))
                    best = min(best, math.hypot(cx - (ax + dx * t), cy - (ay + dy * t)))
            out.append((c, round(best - rf.WEIGHT / 2 - r)))
    return out


def widths():
    seen = {}
    for c in ORDER:
        cs = rf.contours(rf.GLYPHS[c], rf.WEIGHT, rf.CURVE, rf.RADIUS)
        xs = [q[0] for k in cs for q in k]
        seen.setdefault(round(max(xs) - min(xs)), []).append(c)
    return seen


def alignment():
    tops, bots = {}, {}
    for c in ORDER:
        cs = rf.contours(rf.GLYPHS[c], rf.WEIGHT, rf.CURVE, rf.RADIUS)
        ys = [q[1] for k in cs for q in k]
        tops.setdefault(round(max(ys)), []).append(c)
        bots.setdefault(round(min(ys)), []).append(c)
    return tops, bots


def distinct():
    from fontTools.pens.recordingPen import RecordingPen
    sig = {}
    for c in ORDER:
        p = RecordingPen()
        for poly in rf.contours(rf.GLYPHS[c], rf.WEIGHT, rf.CURVE, rf.RADIUS):
            p.moveTo(poly[0])
            for q in poly[1:]:
                p.lineTo(q)
            p.closePath()
        sig.setdefault(repr(p.value), []).append(c)
    return [v for v in sig.values() if len(v) > 1]


def main():
    fails = 0
    print(f"stroke width {rf.WEIGHT}, cap {rf.CAP}\n")

    m = merges()
    print(f"MERGING STROKES — {len(m)} found")
    for c, i, j, d, ov, at in m:
        print(f"   {c}: strokes {i}+{j} within {d} (overlap {ov}) near {at}")
    fails += len(m)

    dc = dot_clearance()
    worst = min(g for _, g in dc) if dc else 99
    print(f"\nDOT CLEARANCE — worst {worst}")
    for c, g in dc:
        if g < 15:
            print(f"   {c}: only {g}")
            fails += 1

    w = widths()
    print(f"\nINK WIDTHS — {len(w)} distinct")
    for k in sorted(w):
        print(f"   {k:5}  {''.join(w[k])}")

    tops, bots = alignment()
    print("\nINK TOP")
    for k in sorted(tops, reverse=True):
        over = "  <-- EXCEEDS THE STAVE" if k > rf.CAP else ""
        print(f"   {k:5}  {''.join(tops[k])}{over}")
        if k > rf.CAP:
            fails += len(tops[k])

    d = distinct()
    print(f"\nDUPLICATE OUTLINES — {len(d)}")
    for grp in d:
        print("   " + " ".join(grp))
    fails += len(d)

    print(f"\n{'PASS' if fails == 0 else str(fails) + ' ISSUE(S)'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

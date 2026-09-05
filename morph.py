#!/usr/bin/env python3
"""Morph one continuous line through every rune.

Each glyph is reduced to a SINGLE polyline -- strokes joined end to end,
dots traversed as little loops -- then resampled to a fixed number of
points by arc length. Because every glyph then has the same point count,
point i of one rune has a counterpart in the next, and the whole
alphabet can be walked as one line reshaping itself.

Outputs an animated SVG (morphing the `d` attribute) and, if Pillow is
present, a GIF built by offsetting the moving centreline with the font's
own geometry, so the line always carries the font's true weight.
"""

import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import runefont as rf
import runes

N = 160                       # points per glyph after resampling
ORDER = "abcdefghijklmnopqrstuvwxyzæøå"


def _strokes(els):
    """Centrelines of one glyph, dots turned into small closed loops."""
    out = []
    for e in els:
        k = e[0]
        if k in ("O", "D"):
            cx, cy, r = e[1], e[2], e[3]
            out.append([(cx + r * math.cos(2 * math.pi * i / 16),
                         cy + r * math.sin(2 * math.pi * i / 16))
                        for i in range(17)])
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
        if closed:
            f = rf._dedupe(rf._fillet_closed(rf._dedupe(pts)[:-1], rf.RADIUS))
            f = f + [f[0]]
        else:
            f = rf._dedupe(rf._fillet(rf._dedupe(pts), rf.RADIUS))
        out.append([(q[0], q[1]) for q in f])
    return out


def _one_line(strokes):
    """Chain the strokes into one path, always hopping to whichever loose
    end is nearest, so the connecting travel stays as short as possible."""
    remaining = [list(s) for s in strokes]
    path = remaining.pop(0)
    while remaining:
        tail = path[-1]
        best, rev, dist = None, False, float("inf")
        for i, s in enumerate(remaining):
            for r in (False, True):
                head = s[-1] if r else s[0]
                d = math.hypot(head[0] - tail[0], head[1] - tail[1])
                if d < dist:
                    best, rev, dist = i, r, d
        s = remaining.pop(best)
        if rev:
            s = s[::-1]
        path += s
    return path


def _resample(pts, n):
    """Even spacing by arc length, so point i means the same thing in
    every glyph and the morph does not bunch up."""
    seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
           for i in range(len(pts) - 1)]
    total = sum(seg) or 1.0
    out, acc, j = [pts[0]], 0.0, 0
    for i in range(1, n):
        target = total * i / (n - 1)
        while j < len(seg) and acc + seg[j] < target:
            acc += seg[j]
            j += 1
        if j >= len(seg):
            out.append(pts[-1])
            continue
        t = (target - acc) / (seg[j] or 1.0)
        a, b = pts[j], pts[j + 1]
        out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def outlines():
    """One resampled, centred polyline per rune."""
    result = {}
    for c in ORDER:
        pts = _resample(_one_line(_strokes(rf.GLYPHS[c])), N)
        xs = [p[0] for p in pts]
        mid = (min(xs) + max(xs)) / 2
        result[c] = [(p[0] - mid, p[1]) for p in pts]   # centre each glyph
    return result


def ease(t):
    return t * t * (3 - 2 * t)


def build_svg(path="dist/morph.svg", hold=0.28, W=560, H=560):
    o = outlines()
    scale = (H * 0.62) / rf.CAP
    def d(pts):
        return "M" + " L".join(f"{W/2 + x*scale:.1f} {H*0.80 - y*scale:.1f}"
                               for x, y in pts)
    seq = [o[c] for c in ORDER] + [o[ORDER[0]]]
    values, times = [], []
    step = 1.0 / (len(seq) - 1)
    for i in range(len(seq)):
        values.append(d(seq[i]))
        times.append(i * step)
        if i < len(seq) - 1:
            values.append(d(seq[i]))
            times.append(min(i * step + step * hold, 1.0))
    dur = len(ORDER) * 0.62
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}"
  width="{W}" height="{H}" role="img" aria-label="En linje som blir til hver rune">
  <title>En linje som blir til hver rune</title>
  <rect width="{W}" height="{H}" fill="#121614" rx="16"/>
  <path fill="none" stroke="#E9ECE8" stroke-width="{rf.WEIGHT*scale:.1f}"
        stroke-linecap="round" stroke-linejoin="round" d="{values[0]}">
    <animate attributeName="d" dur="{dur:.1f}s" repeatCount="indefinite"
      calcMode="spline"
      values="{';'.join(values)}"
      keyTimes="{';'.join(f'{t:.4f}' for t in times)}"
      keySplines="{';'.join(['.45 .05 .25 1'] * (len(values)-1))}"/>
  </path>
</svg>'''
    out = pathlib.Path(__file__).parent / path
    out.write_text(svg, encoding="utf-8")
    print(f"  {path}  ({out.stat().st_size} bytes, {len(ORDER)} runes)")
    return out


def _draw_thick(draw, pts, width, to_px):
    """Paint a thick polyline as a union of capsules.

    Offsetting the whole path and filling it would be wrong here: the line
    doubles back on itself where it travels between strokes, and a
    self-intersecting polygon fills XOR, punching holes in the stroke.
    """
    h = width / 2
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = to_px(pts[i]), to_px(pts[i + 1])
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy)
        if length < 1e-6:
            continue
        nx, ny = -dy / length * h, dx / length * h
        draw.polygon([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
                      (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], fill=255)
    for p_ in pts:                       # round joins and caps
        x, y = to_px(p_)
        draw.ellipse([x - h, y - h, x + h, y + h], fill=255)


def build_gif(path="dist/morph.gif", size=460, fps=20, morph=10, hold=4, ss=2):
    from PIL import Image, ImageDraw
    o = outlines()
    scale = (size * 0.62) / rf.CAP * ss
    W = H = size * ss
    px = lambda p: (W / 2 + p[0] * scale, H * 0.80 - p[1] * scale)
    frames = []
    seq = list(ORDER) + [ORDER[0]]
    for i in range(len(seq) - 1):
        a, b = o[seq[i]], o[seq[i + 1]]
        steps = [0.0] * hold + [ease((f + 1) / morph) for f in range(morph)]
        for t in steps:
            pts = [(a[k][0] + (b[k][0] - a[k][0]) * t,
                    a[k][1] + (b[k][1] - a[k][1]) * t) for k in range(N)]
            mask = Image.new("L", (W, H), 0)
            _draw_thick(ImageDraw.Draw(mask), pts, rf.WEIGHT * scale, px)
            mask = mask.resize((size, size), Image.LANCZOS)
            frame = Image.new("RGB", (size, size), (18, 22, 20))
            frame.paste(Image.new("RGB", (size, size), (233, 236, 232)), (0, 0), mask)
            frames.append(frame.convert("P", palette=Image.ADAPTIVE, colors=8))
    out = pathlib.Path(__file__).parent / path
    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=int(1000 / fps), loop=0, optimize=True)
    print(f"  {path}  ({out.stat().st_size//1024} KB, {len(frames)} frames)")
    return out


if __name__ == "__main__":
    build_svg()
    build_gif()

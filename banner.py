#!/usr/bin/env python3
"""Generate the animated README banner.

GitHub strips <script> from README content, so the animation is SMIL
inside the SVG. It draws the skeleton first and the carved stroke after
it, along the very centrelines the font is built from -- so what the
banner shows is the font's construction, not an impression of it.
"""

import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import runefont as rf

WORD, W, H, DUR, CAP_PX = "runa", 1200, 360, 9.0, 176


def geometry(els):
    cs = rf.contours(els, rf.WEIGHT, rf.CURVE, rf.RADIUS)
    xs = [q[0] for c in cs for q in c]
    minx, maxx = (min(xs), max(xs)) if xs else (0, 0)
    shift = rf.SIDE - minx
    strokes, dots = [], []
    for e in els:
        k = e[0]
        if k in ("O", "D"):
            dots.append((e[1] + shift, e[2], e[3]))
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
        f = [(q[0] + shift, q[1]) for q in f]
        length = sum(math.hypot(f[i + 1][0] - f[i][0], f[i + 1][1] - f[i][1])
                     for i in range(len(f) - 1))
        rounded = (not closed) and any(
            rf._free_end((q[0] - shift, q[1]), False) and abs(q[0] - shift) > rf.WEIGHT / 2
            for q in (f[0], f[-1]))
        strokes.append((f, length, rounded))
    return strokes, dots, maxx - minx + rf.SIDE * 2


def build(path="dist/banner.svg"):
    items, x = [], 0
    for ch in WORD:
        st, do, adv = geometry(rf.GLYPHS[ch])
        items.append((st, do, x))
        x += adv

    scale = CAP_PX / rf.CAP
    ox, oy = (W - x * scale) / 2, 288
    parts = []
    n = sum(len(st) for st, _, _ in items)
    i = 0
    for st, do, gx in items:
        for pts, length, rounded in st:
            d = "M" + " L".join(f"{p[0]:.1f} {p[1]:.1f}" for p in pts)
            t = i / max(n - 1, 1)
            f0, g0 = 0.04 + 0.28 * t, 0.20 + 0.34 * t
            L = f"{length:.1f}"
            cap = "round" if rounded else "butt"
            # A round cap on a fully-offset dash still paints a dot, so each
            # path stays invisible until its own draw begins.
            parts.append(f'''<g transform="translate({gx},0)">
      <path class="guide" d="{d}" stroke-dasharray="{L}" stroke-dashoffset="{L}" opacity="0">
        <animate attributeName="stroke-dashoffset" values="{L};{L};0;0"
          keyTimes="0;{f0:.3f};{f0+0.12:.3f};1" dur="{DUR}s" repeatCount="indefinite"
          calcMode="spline" keySplines="0 0 1 1;.25 .1 .25 1;0 0 1 1"/>
        <animate attributeName="opacity" values="0;0;1;1;0;0"
          keyTimes="0;{max(f0-0.005,0):.3f};{f0:.3f};0.74;0.82;1"
          dur="{DUR}s" repeatCount="indefinite"/>
      </path>
      <path class="carve" d="{d}" stroke-linecap="{cap}"
        stroke-dasharray="{L}" stroke-dashoffset="{L}" opacity="0">
        <animate attributeName="stroke-dashoffset" values="{L};{L};0;0"
          keyTimes="0;{g0:.3f};{g0+0.16:.3f};1" dur="{DUR}s" repeatCount="indefinite"
          calcMode="spline" keySplines="0 0 1 1;.4 .05 .2 1;0 0 1 1"/>
        <animate attributeName="opacity" values="0;0;1;1"
          keyTimes="0;{max(g0-0.005,0):.3f};{g0:.3f};1"
          dur="{DUR}s" repeatCount="indefinite"/>
      </path></g>''')
            i += 1
        for cx, cy, r in do:
            g0 = 0.20 + 0.34 * (min(i, n - 1) / max(n - 1, 1))
            parts.append(f'''<g transform="translate({gx},0)">
      <circle class="dot" cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" opacity="0">
        <animate attributeName="opacity" values="0;0;1;1"
          keyTimes="0;{g0:.3f};{g0+0.05:.3f};1" dur="{DUR}s" repeatCount="indefinite"/>
      </circle></g>''')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}"
  width="{W}" height="{H}" role="img"
  aria-label="Runa - norsk skrevet med middelalderruner">
  <title>Runa - norsk skrevet med middelalderruner</title>
  <style>
    .bg{{fill:#121614}}
    /* stroke-width is in user units, inside the scaled group -- the font's
       own 76, not a pre-scaled pixel value that would scale a second time */
    .carve{{fill:none;stroke:#E9ECE8;stroke-width:{rf.WEIGHT};stroke-linejoin:round}}
    .guide{{fill:none;stroke:#84C39F;stroke-width:9;stroke-linecap:round;stroke-linejoin:round}}
    .dot{{fill:#E9ECE8}}
    .sub{{font-family:system-ui,-apple-system,'Segoe UI',Cantarell,sans-serif;fill:#95A19A}}
    .kicker{{font-family:system-ui,-apple-system,'Segoe UI',Cantarell,sans-serif;
      fill:#84C39F;letter-spacing:3.5px;font-weight:600}}
  </style>
  <rect class="bg" width="{W}" height="{H}" rx="18"/>
  <text class="kicker" x="{W/2}" y="52" font-size="13" text-anchor="middle">MIDDELALDERRUNER FOR NORSK</text>
  <g transform="translate({ox:.1f},{oy:.1f}) scale({scale:.5f},-{scale:.5f})">
    {''.join(parts)}
  </g>
  <text class="sub" x="{W/2}" y="{H-38}" font-size="17" text-anchor="middle">Tastaturoppsett for Linux, macOS og Windows — og en skrifttype bygget av samme skjelett</text>
</svg>
'''
    out = pathlib.Path(__file__).parent / path
    out.write_text(svg, encoding="utf-8")
    print(f"  {path}  ({out.stat().st_size} bytes, {n} strokes)")
    return out


if __name__ == "__main__":
    build()

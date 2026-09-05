#!/usr/bin/env python3
"""Draw every rune, one after another, along the font's own centrelines.

Each rune is drawn stroke by stroke and then retracted, so the line is
always being made rather than reshaped. Strokes are NOT chained into one
path: the travel between them is not part of the letter, and drawing it
would put strokes on screen that the rune does not have.

Dots stay dots. They are placed after their glyph's strokes finish, not
threaded onto the line.

Outputs an animated SVG, a GIF and an MP4.
"""

import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import runefont as rf

ORDER = "abcdefghijklmnopqrstuvwxyzæøå"
DRAW, HOLD, BACK = 8, 4, 5          # frames per phase, per rune
FPS = 22


def glyph(els):
    """(centrelines, dots) for one rune, centred on its own ink."""
    strokes, dots = [], []
    for e in els:
        k = e[0]
        if k in ("O", "D"):
            dots.append([e[1], e[2], e[3]])
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
        strokes.append([(q[0], q[1]) for q in f])

    xs = [q[0] for s in strokes for q in s] + \
         [d[0] + s for d in dots for s in (-d[2], d[2])]
    mid = (min(xs) + max(xs)) / 2
    strokes = [[(x - mid, y) for x, y in s] for s in strokes]
    dots = [[d[0] - mid, d[1], d[2]] for d in dots]
    return strokes, dots


def _length(pts):
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
               for i in range(len(pts) - 1))


def _partial(pts, want):
    """The first `want` units of a polyline."""
    if want <= 0:
        return []
    out, acc = [pts[0]], 0.0
    for i in range(len(pts) - 1):
        seg = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
        if acc + seg >= want:
            t = (want - acc) / (seg or 1.0)
            out.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t,
                        pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t))
            return out
        acc += seg
        out.append(pts[i + 1])
    return out


def drawn(strokes, f):
    """Strokes revealed up to fraction f of the glyph's total ink."""
    total = sum(_length(s) for s in strokes) or 1.0
    want = total * max(0.0, min(1.0, f))
    out, used = [], 0.0
    for s in strokes:
        L = _length(s)
        if used + L <= want:
            out.append(s)
        elif used < want:
            out.append(_partial(s, want - used))
            break
        else:
            break
        used += L
    return [s for s in out if len(s) > 1]


def ease(t):
    return t * t * (3 - 2 * t)


# --- GIF / MP4 --------------------------------------------------------

def _paint(draw, strokes, width, to_px):
    """Union of round-capped capsules. Filling an offset outline would be
    wrong: the shape self-intersects and a self-intersecting polygon fills
    XOR, punching holes through the stroke."""
    h = width / 2
    for pts in strokes:
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = to_px(pts[i]), to_px(pts[i + 1])
            dx, dy = x1 - x0, y1 - y0
            length = math.hypot(dx, dy)
            if length < 1e-6:
                continue
            nx, ny = -dy / length * h, dx / length * h
            draw.polygon([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
                          (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], fill=255)
        for p in pts:
            x, y = to_px(p)
            draw.ellipse([x - h, y - h, x + h, y + h], fill=255)


def build_gif(path="dist/alphabet.gif", size=460, ss=2):
    from PIL import Image, ImageDraw
    scale = (size * 0.62) / rf.CAP * ss
    W = H = size * ss
    px = lambda p: (W / 2 + p[0] * scale, H * 0.80 - p[1] * scale)
    frames = []
    for c in ORDER:
        strokes, dots = glyph(rf.GLYPHS[c])
        phases = ([ease((i + 1) / DRAW) for i in range(DRAW)] +
                  [1.0] * HOLD +
                  [1.0 - ease((i + 1) / BACK) for i in range(BACK)])
        for n, f in enumerate(phases):
            mask = Image.new("L", (W, H), 0)
            d = ImageDraw.Draw(mask)
            _paint(d, drawn(strokes, f), rf.WEIGHT * scale, px)
            if f >= 1.0:                       # dots land once the line is done
                for cx, cy, r in dots:
                    x, y = px((cx, cy))
                    d.ellipse([x - r * scale, y - r * scale,
                               x + r * scale, y + r * scale], fill=255)
            mask = mask.resize((size, size), Image.LANCZOS)
            frame = Image.new("RGB", (size, size), (18, 22, 20))
            frame.paste(Image.new("RGB", (size, size), (233, 236, 232)), (0, 0), mask)
            frames.append(frame.convert("P", palette=Image.ADAPTIVE, colors=8))
    out = pathlib.Path(__file__).parent / path
    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=int(1000 / FPS), loop=0, optimize=True)
    print(f"  {path}  ({out.stat().st_size//1024} KB, {len(frames)} frames)")
    return out


# --- SVG --------------------------------------------------------------

def build_svg(path="dist/alphabet.svg", W=520, H=520):
    scale = (H * 0.62) / rf.CAP
    px = lambda p: (W / 2 + p[0] * scale, H * 0.80 - p[1] * scale)
    per = (DRAW + HOLD + BACK) / FPS
    dur = per * len(ORDER)
    body = []
    for gi, c in enumerate(ORDER):
        strokes, dots = glyph(rf.GLYPHS[c])
        t0 = gi * per / dur
        draw_end = t0 + (DRAW / FPS) / dur
        back_0 = t0 + ((DRAW + HOLD) / FPS) / dur
        back_1 = t0 + ((DRAW + HOLD + BACK) / FPS) / dur
        lens = [_length(s) for s in strokes]
        total = sum(lens) or 1.0
        acc = 0.0
        for s, L in zip(strokes, lens):
            a = t0 + (draw_end - t0) * (acc / total)
            b = t0 + (draw_end - t0) * ((acc + L) / total)
            ra = back_0 + (back_1 - back_0) * (1 - (acc + L) / total)
            rb = back_0 + (back_1 - back_0) * (1 - acc / total)
            acc += L
            d = "M" + " L".join(f"{px(p)[0]:.1f} {px(p)[1]:.1f}" for p in s)
            Ls = f"{L*scale:.1f}"
            body.append(f'''<path class="ln" d="{d}" stroke-dasharray="{Ls}"
      stroke-dashoffset="{Ls}" opacity="0">
      <animate attributeName="stroke-dashoffset"
        values="{Ls};{Ls};0;0;{Ls};{Ls}"
        keyTimes="0;{a:.4f};{b:.4f};{ra:.4f};{rb:.4f};1"
        dur="{dur:.1f}s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0;0;1;1;0;0"
        keyTimes="0;{max(a-0.001,0):.4f};{a:.4f};{rb:.4f};{min(rb+0.001,1):.4f};1"
        dur="{dur:.1f}s" repeatCount="indefinite"/></path>''')
        for cx, cy, r in dots:
            x, y = px((cx, cy))
            body.append(f'''<circle class="dt" cx="{x:.1f}" cy="{y:.1f}"
      r="{r*scale:.1f}" opacity="0">
      <animate attributeName="opacity" values="0;0;1;1;0;0"
        keyTimes="0;{draw_end:.4f};{min(draw_end+0.004,1):.4f};{back_0:.4f};{min(back_0+0.004,1):.4f};1"
        dur="{dur:.1f}s" repeatCount="indefinite"/></circle>''')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}"
  width="{W}" height="{H}" role="img" aria-label="Hver rune tegnes etter tur">
  <title>Hver rune tegnes etter tur</title>
  <style>
    .ln{{fill:none;stroke:#E9ECE8;stroke-width:{rf.WEIGHT*scale:.1f};
      stroke-linecap:round;stroke-linejoin:round}}
    .dt{{fill:#E9ECE8}}
  </style>
  <rect width="{W}" height="{H}" fill="#121614" rx="16"/>
  {''.join(body)}
</svg>'''
    out = pathlib.Path(__file__).parent / path
    out.write_text(svg, encoding="utf-8")
    print(f"  {path}  ({out.stat().st_size//1024} KB, {dur:.1f}s loop)")
    return out


if __name__ == "__main__":
    build_svg()
    build_gif()

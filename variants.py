#!/usr/bin/env python3
"""Generate numbered font variants across the configuration space.

Each variant is a dict of overrides applied to runefont's module options,
built into its own TTF. The list below is curated rather than a full cross
product -- each row changes something visible and is worth comparing.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

VARIANTS = [
    (1,  "Standard",              {}),
    (2,  "Lett",                  {"WEIGHT": 56}),
    (3,  "Tung",                  {"WEIGHT": 100}),
    (4,  "Skarpe hjørner",        {"RADIUS": 0}),
    (5,  "Myke hjørner",          {"RADIUS": 110}),
    (6,  "Smal (rekkevidde 299)", {"_SCALE": 0.74}),
    (7,  "Bred og luftig",        {"SIDE": 190}),
    (8,  "Frittstående lemmer",   {"DETACH": 40}),
    (9,  "Sterkt frittstående",   {"DETACH": 80}),
    (10, "Seriffer",              {"SERIF": True}),
    (11, "Seriffer + lett",       {"SERIF": True, "WEIGHT": 56, "SERIF_LEN": 130}),
    (12, "Frittstående + serif",  {"DETACH": 40, "SERIF": True}),
    (13, "Fulle boller",          {"BP_SPACE": 0, "BP_MIDDLE": "merge"}),
    (14, "Flytende j, ring-tegn", {"J_STYLE": "float", "PUNCT_DOT": "ring"}),
    (15, "Tett og tung",          {"WEIGHT": 100, "SIDE": 70, "RADIUS": 20}),
    (16, "Tynn, myk, luftig",     {"WEIGHT": 48, "RADIUS": 130, "SIDE": 200,
                                   "DETACH": 30}),
]

SCALED = {"ONE_M, ONE_W": (404, 564), "SYM_M, SYM_W": (202, 282),
          "STUB_N, STUB_R_N": (164, 82), "STUB_M, STUB_R_M": (202, 101)}


def build_variant(no, name, overrides, outdir):
    """Apply overrides at SOURCE level and re-exec.

    setattr after import is not enough: build()'s defaults and every
    derived value (_BP_*, _J, _MARK...) are computed when the module body
    runs, so the options must be changed before that happens.
    """
    import re
    src = pathlib.Path(__file__).parent.joinpath("runefont.py").read_text()
    scale = overrides.pop("_SCALE", None)
    for key, val in overrides.items():
        rep = f'{key} = {val!r}'
        src, n = re.subn(rf"^{key} = .*?(#|$)", lambda m: rep + "  " + (m.group(1) or ""),
                         src, count=1, flags=re.M)
        assert n == 1, f"option {key} not found"
    if scale:
        for pair, vals in SCALED.items():
            rep = f"{pair} = {round(vals[0]*scale)}, {round(vals[1]*scale)}"
            src, n = re.subn(rf"^{re.escape(pair)} = .*$", rep, src, count=1, flags=re.M)
            assert n == 1, pair
        src, n = re.subn(r"^GAP = \d+", f"GAP = {round(160*scale)}", src, count=1, flags=re.M)
        assert n == 1
    ns = {"__name__": "variant",
          "__file__": str(pathlib.Path(__file__).parent / "runefont.py")}
    exec(compile(src, f"runefont_v{no}", "exec"), ns)
    path = pathlib.Path(outdir) / f"Runa-V{no:02d}.ttf"
    ns["build"](str(path), family=f"Runa V{no:02d}", weight=ns["WEIGHT"],
                curve=ns["CURVE"], radius=ns["RADIUS"], side=ns["SIDE"])
    return path


def main(outdir="dist/variants"):
    out = pathlib.Path(__file__).parent / outdir
    out.mkdir(parents=True, exist_ok=True)
    for no, name, ov in VARIANTS:
        p = build_variant(no, name, dict(ov), out)
        print(f"  {no:2d}  {name:24s} {p.name}")
    return VARIANTS


if __name__ == "__main__":
    main()

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
    # The default skeleton is hybrid: diagonal arms and stubs, curved
    # bowls and arches. Ny-europeisk (all-orthogonal) is kept as its own
    # explicit variant.
    (1,  "Ny-europeisk",          {"SKELETON": "neweuropean"}),
    (2,  "Lett",                  {"WEIGHT": 56}),
    (3,  "Tung",                  {"WEIGHT": 100}),
    (4,  "Skarpe hjørner",        {"RADIUS": 0}),
    (5,  "Myke hjørner",          {"RADIUS": 110}),
    (6,  "Smal (rekkevidde 299)", {"_SCALE": 0.74}),
    (7,  "Bred og luftig",        {"SIDE": 190}),
    (8,  "Frittstående lemmer",   {"DETACH": 40}),
    (9,  "Sterkt frittstående",   {"DETACH": 80}),
    (10, "Skrivemaskin",          {"SERIF": True}),
    (11, "Seriffer + lett",       {"SERIF": True, "WEIGHT": 56, "SERIF_LEN": 130}),
    (12, "Frittstående + serif",  {"DETACH": 40, "SERIF": True}),
    (13, "Fulle boller",          {"BP_SPACE": 0, "BP_MIDDLE": "merge"}),
    (14, "Flytende j, ring-tegn", {"J_STYLE": "float", "PUNCT_DOT": "ring"}),
    (15, "Tett og tung",          {"WEIGHT": 100, "SIDE": 70, "RADIUS": 20}),
    (16, "Tynn, myk, luftig",     {"WEIGHT": 48, "RADIUS": 130, "SIDE": 200,
                                   "DETACH": 30}),
    (17, "Antikva",               {"SERIF": True, "SERIF_STYLE": "bracketed",
                                   "CONTRAST": 0.55, "WEIGHT": 88}),
    (18, "Antikva lett",          {"SERIF": True, "SERIF_STYLE": "bracketed",
                                   "CONTRAST": 0.45, "WEIGHT": 68,
                                   "SERIF_LEN": 125}),
    (19, "Gammelantikva",         {"SERIF": True, "SERIF_STYLE": "bracketed",
                                   "CONTRAST": 0.52, "WEIGHT": 88,
                                   "STRESS_ANGLE": -20}),
    (20, "Gammelantikva lett",    {"SERIF": True, "SERIF_STYLE": "bracketed",
                                   "CONTRAST": 0.45, "WEIGHT": 68,
                                   "STRESS_ANGLE": -20, "SERIF_LEN": 125}),
    (21, "Tradisjonell",          {"SKELETON": "traditional"}),
    (22, "Tradisjonell lett",     {"SKELETON": "traditional", "WEIGHT": 56}),
    (23, "Tradisjonell antikva",  {"SKELETON": "traditional", "SERIF": True,
                                   "SERIF_STYLE": "bracketed", "CONTRAST": 0.55,
                                   "WEIGHT": 88}),
    (24, "Hybrid",                {"SKELETON": "hybrid"}),
    (25, "Ny-europeisk antikva",  {"SKELETON": "neweuropean", "SERIF": True,
                                   "SERIF_STYLE": "bracketed", "CONTRAST": 0.55,
                                   "WEIGHT": 88}),
    (26, "Digital skarp",         {"DOT_SHAPE": "square", "CORNER_STYLE": "chamfer",
                                   "RADIUS": 80, "END_CAPS": "flat", "WEIGHT": 82,
                                   "TIP_SLICE": True}),
    (27, "Digital rund",          {"DOT_SHAPE": "square", "RADIUS": 60,
                                   "TIP_SLICE": True}),
    (28, "Stempel",               {"DETACH": 55, "RADIUS": 0, "END_CAPS": "flat",
                                   "DOT_SHAPE": "square", "WEIGHT": 92,
                                   "TIP_SLICE": True}),
]

# Families that also ship bold and italic companions, built from the same
# config with the weight raised or the glyph sheared.
STYLED = {1: "bi", 2: "bi", 3: "i", 10: "b", 17: "bi", 18: "bi", 19: "bi",
          20: "bi", 21: "bi", 23: "bi", 24: "bi", 25: "bi",
          26: "b", 27: "b", 28: "b"}


def build_styled(outdir="dist/variants"):
    out = pathlib.Path(__file__).parent / outdir
    for no, name, ov in VARIANTS:
        flags = STYLED.get(no, "")
        if "b" in flags:
            b = dict(ov); b["WEIGHT"] = ov.get("WEIGHT", 76) + 26
            build_variant(no, name, b, out, suffix="-Bold")
        if "i" in flags:
            i = dict(ov); i["SLANT"] = 12
            build_variant(no, name, i, out, suffix="-Italic")
        if flags:
            print(f"  {no:2d} {name}: {'fet ' if 'b' in flags else ''}{'kursiv' if 'i' in flags else ''}")


SCALED = {"ONE_M, ONE_W": (404, 564), "SYM_M, SYM_W": (202, 282),
          "STUB_N, STUB_R_N": (164, 82), "STUB_M, STUB_R_M": (202, 101)}


def build_variant(no, name, overrides, outdir, suffix=""):
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
    path = pathlib.Path(outdir) / f"Runa-V{no:02d}{suffix}.ttf"
    fam = f"Runa V{no:02d}" + suffix.replace("-", " ")
    ns["build"](str(path), family=fam, weight=ns["WEIGHT"],
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
    build_styled()

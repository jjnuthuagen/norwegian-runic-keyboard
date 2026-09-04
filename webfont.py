"""Subset Noto Sans Runic down to the runes we actually use, and inline it.

macOS ships no runic font at all and many phones ship none either, so a
page that merely *asks* for a runic family renders empty boxes for a large
share of visitors. Embedding the glyphs is the difference between the
cheat sheet working for the people it is meant for and not.

The full face is only ~10KB, and the subset is smaller still, so this
costs almost nothing. woff2 would be smaller again but needs brotli,
which is not a dependency worth adding for a few KB.
"""

import base64
import io
import pathlib

import runes

SOURCES = [
    "/usr/share/fonts/noto/NotoSansRunic-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansRunic-Regular.ttf",
    "/usr/share/fonts/TTF/NotoSansRunic-Regular.ttf",
]

CACHE = pathlib.Path(__file__).parent / "dist" / "web" / "runic-subset.b64"


def glyphs():
    """Every rune the layouts can produce, plus the three dividers."""
    chars = set()
    for _latin, base, shift, *_ in runes.ALL_KEYS:
        chars.update(ch for ch in (base + shift) if ord(ch) >= 0x16A0)
    chars.update(runes.PUNCTUATION)
    return "".join(sorted(chars))


def _subset_bytes():
    from fontTools import subset
    from fontTools.ttLib import TTFont

    src = next((p for p in SOURCES if pathlib.Path(p).exists()), None)
    if src is None:
        raise FileNotFoundError(
            "Noto Sans Runic not found. Install it (package noto-fonts) or "
            "drop NotoSansRunic-Regular.ttf next to this file."
        )

    font = TTFont(src)
    options = subset.Options()
    options.layout_features = ["*"]
    options.notdef_outline = True
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text=glyphs())
    subsetter.subset(font)

    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


def data_uri(refresh=False):
    """base64 TTF data URI. Cached so the generated pages are reproducible
    on machines without the font installed."""
    if CACHE.exists() and not refresh:
        return CACHE.read_text().strip()
    raw = _subset_bytes()
    uri = "data:font/ttf;base64," + base64.b64encode(raw).decode("ascii")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(uri)
    return uri


def css(refresh=False):
    return (
        "@font-face{font-family:'RunicSubset';"
        f"src:url({data_uri(refresh)}) format('truetype');"
        "font-display:swap;font-weight:400;font-style:normal}"
    )


if __name__ == "__main__":
    chars = glyphs()
    uri = data_uri(refresh=True)
    print(f"{len(chars)} glyphs subset: {chars}")
    print(f"data URI {len(uri)} chars (~{len(uri)//1024}KB inlined)")

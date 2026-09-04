#!/usr/bin/env python3
"""Generate the printable cheat sheet from runes.py.

One A4 page. The point of the layout is that it is a picture of the
keyboard, not an alphabetical list -- you look up a rune by finding the
key your finger is already on.
"""

import pathlib
import subprocess

import runes
import webfont

OUT = pathlib.Path(__file__).parent / "dist" / "cheatsheet"

# Physical rows, in the order they sit on a Norwegian pc105 board.
ROWS = [
    [k for k in runes.ALL_KEYS if k[3].startswith("AD")],
    [k for k in runes.ALL_KEYS if k[3].startswith("AC")],
    [k for k in runes.ALL_KEYS if k[3].startswith("AB")],
]

CSS = """
:root{
  --ground:#F1F2EF; --panel:#FFFFFF; --ink:#191C1A; --muted:#6B756F;
  --rule:#CBCFC8; --accent:#2F6E4F; --accent-soft:#E0EBE3;
}
@media (prefers-color-scheme:dark){
  :root{--ground:#141816; --panel:#1B201D; --ink:#E8EBE7; --muted:#94A099;
        --rule:#333A36; --accent:#7FBE9B; --accent-soft:#20302A;}
}
:root[data-theme="dark"]{
  --ground:#141816; --panel:#1B201D; --ink:#E8EBE7; --muted:#94A099;
  --rule:#333A36; --accent:#7FBE9B; --accent-soft:#20302A;
}
:root[data-theme="light"]{
  --ground:#F1F2EF; --panel:#FFFFFF; --ink:#191C1A; --muted:#6B756F;
  --rule:#CBCFC8; --accent:#2F6E4F; --accent-soft:#E0EBE3;
}
*{box-sizing:border-box}
body{
  margin:0; padding:14mm 12mm; background:var(--ground); color:var(--ink);
  font-family:system-ui,-apple-system,"Segoe UI",Cantarell,"Noto Sans",sans-serif;
  font-size:10pt; line-height:1.45;
}
.sheet{max-width:190mm;margin:0 auto;display:flex;flex-direction:column;gap:7mm}
h1{
  font-family:Georgia,"Iowan Old Style",Palatino,"Book Antiqua",serif;
  font-size:24pt; font-weight:400; margin:0; letter-spacing:-.01em;
  text-wrap:balance;
}
.lede{margin:0;color:var(--muted);max-width:62ch}
.rune-strip{
  font-family:'RunicSubset',serif; font-size:19pt; color:var(--accent);
  letter-spacing:.14em; margin:0; word-break:break-all;
}
.eyebrow{
  font-size:7.5pt; text-transform:uppercase; letter-spacing:.13em;
  color:var(--muted); margin:0 0 2mm;
}
/* keyboard ------------------------------------------------------------ */
.board{display:flex;flex-direction:column;gap:2.4mm}
.row{display:flex;gap:2.4mm}
.row:nth-child(2){margin-left:5mm}
.row:nth-child(3){margin-left:11mm}
.key{
  position:relative; width:15.2mm; height:15.2mm; flex:none;
  background:var(--panel); border:1px solid var(--rule); border-radius:1.6mm;
  display:flex; align-items:center; justify-content:center;
}
.key .base{
  font-family:'RunicSubset',serif; font-size:17pt; line-height:1;
  color:var(--ink);
}
.key .latin{
  position:absolute; top:1mm; left:1.6mm; font-size:7.5pt; font-weight:600;
  color:var(--accent); text-transform:uppercase;
}
.key .shift{
  position:absolute; bottom:.8mm; right:1.6mm;
  font-family:'RunicSubset',serif; font-size:9.5pt; color:var(--muted);
}
.key.punct .base{font-family:inherit;font-size:12pt;color:var(--muted)}
.legend{display:flex;gap:6mm;flex-wrap:wrap;color:var(--muted);font-size:8.5pt}
.legend b{color:var(--accent);font-weight:600}
/* variants ------------------------------------------------------------ */
.cols{display:grid;grid-template-columns:1fr 1fr;gap:6mm}
table{border-collapse:collapse;width:100%;font-size:8.5pt}
td{border-bottom:1px solid var(--rule);padding:1.1mm 0;vertical-align:baseline}
td.r{font-family:'RunicSubset',serif;font-size:13pt;width:7mm;line-height:1}
td.k{width:9mm;color:var(--accent);font-weight:600}
td.n{color:var(--muted)}
.note{
  border-top:1px solid var(--rule); padding-top:3mm; color:var(--muted);
  font-size:8.5pt; display:grid; grid-template-columns:1fr 1fr; gap:5mm;
}
.note p{margin:0}
.note b{color:var(--ink);font-weight:600}
@page{size:A4;margin:0}
@media print{
  body{background:#fff;padding:12mm}
  :root{--ground:#fff;--panel:#fff}
  .key{border-color:#B9BEB7}
}
"""


def key_html(k):
    latin, base, shift, _xkb, _mac, _sc, _vk, _note = k
    punct = " punct" if latin in ",.-" else ""
    return (
        f'<div class="key{punct}"><span class="latin">{latin}</span>'
        f'<span class="base">{base}</span>'
        f'<span class="shift">{shift}</span></div>'
    )


def build(pdf=True):
    board = "\n".join(
        '<div class="row">' + "".join(key_html(k) for k in row) + "</div>"
        for row in ROWS
    )

    alphabet = "".join(runes.TABLE[c] for c in "abcdefghijklmnopqrstuvwxyzæøå")

    variants = [k for k in runes.KEYS]
    half = (len(variants) + 1) // 2

    def table(chunk):
        rows = "".join(
            f'<tr><td class="k">{k[0]}</td><td class="r">{k[2]}</td>'
            f'<td class="n">{k[7]}</td></tr>'
            for k in chunk
        )
        return f"<table>{rows}</table>"

    html = f"""<!doctype html>
<html lang="nb"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Runetastatur — jukselapp</title>
<style>{webfont.css()}{CSS}</style>
</head><body><div class="sheet">

<header>
  <h1>Norsk med middelalderruner</h1>
  <p class="lede">Hver norsk bokstav ligger på tasten du allerede bruker —
  æ, ø og å inkludert. Skift gir runetegn og varianter fra yngre futhark.</p>
  <p class="rune-strip">{alphabet}</p>
</header>

<section>
  <p class="eyebrow">Tastaturet</p>
  <div class="board">{board}</div>
  <p class="legend">
    <span><b>A</b> bokstaven du trykker</span>
    <span><span style="font-family:'RunicSubset'">ᛆ</span> runen du får</span>
    <span><span style="font-family:'RunicSubset'">ᚨ</span> med skift</span>
  </p>
</section>

<section>
  <p class="eyebrow">Skiftnivå — varianter og skilletegn</p>
  <div class="cols">{table(variants[:half])}{table(variants[half:])}</div>
</section>

<div class="note">
  <p><b>Prikkede runer</b> er middelalderens nyvinning: ᚵ er ᚴ med prikk
  (k→g), ᛑ er ᛏ med prikk (t→d), ᛔ er ᛒ (b→p), ᚡ er ᚠ (f→v), ᛂ er ᛁ (i→e).
  Slik fikk skriverne tilbake skillene de 16 runene i yngre futhark hadde
  mistet.</p>
  <p><b>Å er oppdiktet.</b> Bokstaven fantes ikke før rettskrivningen av
  1917 — den kom av lang a, som skriverne skrev med o-runen. Her ligger den
  på ᚭ. Alle andre plasser i tabellen er belagt i faktiske innskrifter.
  Middelalderruner var aldri standardisert.</p>
</div>

</div></body></html>
"""
    OUT.mkdir(parents=True, exist_ok=True)
    page = OUT / "runic-cheatsheet.html"
    page.write_text(html, encoding="utf-8")
    print(f"  {page.relative_to(OUT.parent.parent)}  ({len(html)} bytes)")

    if pdf:
        target = OUT / "runic-cheatsheet.pdf"
        try:
            subprocess.run(
                ["chromium", "--headless", "--disable-gpu", "--no-sandbox",
                 "--no-pdf-header-footer", f"--print-to-pdf={target}",
                 page.as_uri()],
                check=True, capture_output=True, timeout=90,
            )
            print(f"  {target.relative_to(OUT.parent.parent)}  "
                  f"({target.stat().st_size} bytes)")
        except (subprocess.CalledProcessError, FileNotFoundError,
                subprocess.TimeoutExpired) as exc:
            print(f"  PDF skipped ({type(exc).__name__}); open the HTML and print to PDF")


if __name__ == "__main__":
    build()

#!/usr/bin/env python3
"""Generate the rune-reading game as one self-contained HTML file.

Runes are shown, the player types the Norwegian word back. That direction
is deliberate: reading is the skill that transfers to actual inscriptions,
and it works on a phone, where the player has no runic keyboard.

The audience is Norwegian, so words are never translated -- that would be
patronising and would turn a reading drill into a vocabulary test.
"""

import json
import pathlib

import runes
import webfont

OUT = pathlib.Path(__file__).parent / "dist" / "web"

# Graded by length, since length is what actually makes a word hard to
# decode rune by rune. All common enough that a Norwegian reader will
# recognise the word the moment the letters land.
WORDS = {
    1: "sol ost bok hus katt hund fisk snø regn vind natt dag ord navn takk "
       "hei god stor ny øy båt tre fot øye hånd ild hest sau rev elg ku is "
       "arm ben ring gull sang bror mor far sønn".split(),
    2: "måne fjell vann brød melk skog hjerte munn hode jord luft stein "
       "blomst fugl bjørn ulv laks seil fjord gate land konge sverd skip "
       "rune stav barn venn mann kvinne varm kald gammel liten".split(),
    3: "sommer vinter høst kjærlighet dronning skjold bibliotek kunnskap "
       "vennskap fjellet havet skogen vinteren sommeren nordmann språket "
       "historie mørket lyset drømmen minnet".split(),
}
# Deduplicate while keeping the graded order stable.
WORDS = {k: sorted(dict.fromkeys(v)) for k, v in WORDS.items()}

PAGE = r"""<!doctype html>
<html lang="nb"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Runespill — les norsk med middelalderruner</title>
<style>
__FONT__
:root{
  --ground:#F1F2EF; --panel:#FFFFFF; --ink:#191C1A; --muted:#6B756F;
  --rule:#CBCFC8; --accent:#2F6E4F; --accent-soft:#E0EBE3;
  --bad:#9B3B2E; --bad-soft:#F2E0DC;
}
@media (prefers-color-scheme:dark){
  :root{--ground:#141816;--panel:#1B201D;--ink:#E8EBE7;--muted:#94A099;
        --rule:#333A36;--accent:#7FBE9B;--accent-soft:#20302A;
        --bad:#E08A7A;--bad-soft:#3A2420;}
}
:root[data-theme="dark"]{
  --ground:#141816;--panel:#1B201D;--ink:#E8EBE7;--muted:#94A099;
  --rule:#333A36;--accent:#7FBE9B;--accent-soft:#20302A;
  --bad:#E08A7A;--bad-soft:#3A2420;
}
:root[data-theme="light"]{
  --ground:#F1F2EF;--panel:#FFFFFF;--ink:#191C1A;--muted:#6B756F;
  --rule:#CBCFC8;--accent:#2F6E4F;--accent-soft:#E0EBE3;
  --bad:#9B3B2E;--bad-soft:#F2E0DC;
}
*{box-sizing:border-box}
body{
  margin:0;padding:clamp(16px,4vw,40px);background:var(--ground);color:var(--ink);
  font-family:system-ui,-apple-system,"Segoe UI",Cantarell,"Noto Sans",sans-serif;
  line-height:1.5;display:flex;justify-content:center;
}
.wrap{width:100%;max-width:640px;display:flex;flex-direction:column;gap:28px}
header{display:flex;flex-direction:column;gap:6px}
h1{
  font-family:Georgia,"Iowan Old Style",Palatino,serif;font-weight:400;
  font-size:clamp(24px,5vw,32px);margin:0;letter-spacing:-.01em;text-wrap:balance;
}
.lede{margin:0;color:var(--muted);max-width:58ch}
.eyebrow{
  font-size:11px;text-transform:uppercase;letter-spacing:.14em;
  color:var(--muted);margin:0;
}
/* board ------------------------------------------------------------- */
.card{
  background:var(--panel);border:1px solid var(--rule);border-radius:10px;
  padding:clamp(20px,5vw,32px);display:flex;flex-direction:column;gap:20px;
}
.word{
  font-family:'RunicSubset',serif;font-size:clamp(38px,11vw,64px);
  line-height:1.25;letter-spacing:.1em;text-align:center;color:var(--ink);
  word-break:break-word;min-height:1.25em;
}
.word.shake{animation:shake .32s}
@keyframes shake{
  0%,100%{transform:translateX(0)}25%{transform:translateX(-6px)}
  75%{transform:translateX(6px)}
}
form{display:flex;gap:10px;flex-wrap:wrap}
input[type=text]{
  flex:1 1 200px;min-width:0;font:inherit;font-size:18px;padding:12px 14px;
  border:1px solid var(--rule);border-radius:8px;background:var(--ground);
  color:var(--ink);
}
input[type=text]:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
button{
  font:inherit;font-weight:600;padding:12px 20px;border-radius:8px;
  border:1px solid transparent;background:var(--accent);color:var(--panel);
  cursor:pointer;
}
button.ghost{background:transparent;border-color:var(--rule);color:var(--muted)}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.feedback{min-height:64px;display:flex;flex-direction:column;gap:8px}
.pairs{display:flex;gap:4px;flex-wrap:wrap;justify-content:center}
.pair{display:flex;flex-direction:column;align-items:center;min-width:26px}
.pair .r{font-family:'RunicSubset',serif;font-size:26px;line-height:1.1}
.pair .l{font-size:13px;font-weight:600;color:var(--muted)}
.pair.hit .r,.pair.hit .l{color:var(--accent)}
.pair.miss .r,.pair.miss .l{color:var(--bad)}
.msg{text-align:center;font-weight:600}
.msg.good{color:var(--accent)}
.msg.bad{color:var(--bad)}
/* stats -------------------------------------------------------------- */
.stats{display:flex;gap:10px;flex-wrap:wrap}
.stat{
  flex:1 1 0;min-width:90px;background:var(--panel);border:1px solid var(--rule);
  border-radius:8px;padding:12px 14px;display:flex;flex-direction:column;gap:2px;
}
.stat b{font-size:22px;font-weight:600;font-variant-numeric:tabular-nums}
.stat span{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted)}
/* key ---------------------------------------------------------------- */
details{border:1px solid var(--rule);border-radius:10px;background:var(--panel)}
summary{padding:14px 18px;cursor:pointer;font-weight:600}
summary:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.key{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(56px,1fr));
  gap:8px;padding:0 18px 18px;
}
.key div{
  border:1px solid var(--rule);border-radius:6px;padding:6px;text-align:center;
}
.key .r{font-family:'RunicSubset',serif;font-size:22px;line-height:1.2}
.key .l{font-size:12px;color:var(--accent);font-weight:600;text-transform:uppercase}
footer{color:var(--muted);font-size:13px}
footer a{color:var(--accent)}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
</head><body>
<div class="wrap">
  <header>
    <h1>Kan du lese runer?</h1>
    <p class="lede">Ordet står i middelalderruner. Skriv det på norsk.
      Ordene blir lengre jo bedre du gjør det.</p>
  </header>

  <div class="card">
    <div class="word" id="word" aria-live="polite"></div>
    <form id="form" autocomplete="off">
      <input type="text" id="answer" placeholder="skriv ordet her"
             autocomplete="off" autocorrect="off" autocapitalize="off"
             spellcheck="false" aria-label="Ditt svar">
      <button type="submit">Sjekk</button>
      <button type="button" class="ghost" id="skip">Hopp over</button>
    </form>
    <div class="feedback" id="feedback"></div>
  </div>

  <div class="stats">
    <div class="stat"><b id="s-score">0</b><span>Riktige</span></div>
    <div class="stat"><b id="s-streak">0</b><span>På rad</span></div>
    <div class="stat"><b id="s-best">0</b><span>Beste</span></div>
    <div class="stat"><b id="s-level">1</b><span>Nivå</span></div>
  </div>

  <details>
    <summary>Runealfabetet</summary>
    <div class="key" id="key"></div>
  </details>

  <footer>Middelalderruner, ca. 1100–1400. Strengt 1:1 med det norske
  alfabetet, så det kan leses begge veier.</footer>
</div>

<script>
const TABLE = __TABLE__;
const WORDS = __WORDS__;

const $ = id => document.getElementById(id);
const toRunes = w => [...w].map(c => TABLE[c] || c).join("");

let level = 1, score = 0, streak = 0, best = 0, current = "", pool = [];

function refillPool(){
  const words = WORDS[level] || WORDS[3];
  pool = words.slice();
  for (let i = pool.length - 1; i > 0; i--){          // Fisher-Yates, so a
    const j = Math.floor(Math.random() * (i + 1));    // session does not
    [pool[i], pool[j]] = [pool[j], pool[i]];          // repeat words
  }
}

function nextWord(){
  if (!pool.length) refillPool();
  current = pool.pop();
  $("word").textContent = toRunes(current);
  $("answer").value = "";
  $("answer").focus();
}

function renderPairs(word, typed){
  const pairs = [...word].map((ch, i) => {
    const ok = (typed[i] || "").toLowerCase() === ch;
    return `<div class="pair ${ok ? "hit" : "miss"}">
      <span class="r">${TABLE[ch] || ch}</span><span class="l">${ch}</span></div>`;
  }).join("");
  return `<div class="pairs">${pairs}</div>`;
}

function setStats(){
  $("s-score").textContent = score;
  $("s-streak").textContent = streak;
  $("s-best").textContent = best;
  $("s-level").textContent = level;
}

function check(e){
  e.preventDefault();
  const typed = $("answer").value.trim().toLowerCase();
  if (!typed) return;
  const fb = $("feedback");

  if (typed === current){
    score++; streak++; best = Math.max(best, streak);
    // Three in a row promotes; the jump in word length is the reward.
    if (streak && streak % 3 === 0 && level < 3){ level++; refillPool(); }
    fb.innerHTML = `<p class="msg good">Riktig — ${current}</p>`;
    setStats();
    setTimeout(nextWord, 550);
  } else {
    streak = 0;
    if (level > 1) { level--; refillPool(); }
    fb.innerHTML = renderPairs(current, typed) +
      `<p class="msg bad">Ordet var «${current}»</p>`;
    $("word").classList.remove("shake");
    void $("word").offsetWidth;               // restart the animation
    $("word").classList.add("shake");
    setStats();
    setTimeout(nextWord, 2200);
  }
}

$("form").addEventListener("submit", check);
$("skip").addEventListener("click", () => {
  streak = 0;
  $("feedback").innerHTML = renderPairs(current, "") +
    `<p class="msg bad">Ordet var «${current}»</p>`;
  setStats();
  setTimeout(nextWord, 1800);
});

$("key").innerHTML = Object.entries(TABLE).map(([l, r]) =>
  `<div><div class="r">${r}</div><div class="l">${l}</div></div>`).join("");

refillPool(); nextWord(); setStats();
</script>
</body></html>
"""


INDEX = r"""<!doctype html>
<html lang="nb"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Norsk med middelalderruner</title>
<style>
__FONT__
:root{--ground:#F1F2EF;--panel:#FFF;--ink:#191C1A;--muted:#6B756F;
      --rule:#CBCFC8;--accent:#2F6E4F}
@media (prefers-color-scheme:dark){:root{--ground:#141816;--panel:#1B201D;
      --ink:#E8EBE7;--muted:#94A099;--rule:#333A36;--accent:#7FBE9B}}
:root[data-theme="dark"]{--ground:#141816;--panel:#1B201D;--ink:#E8EBE7;
      --muted:#94A099;--rule:#333A36;--accent:#7FBE9B}
:root[data-theme="light"]{--ground:#F1F2EF;--panel:#FFF;--ink:#191C1A;
      --muted:#6B756F;--rule:#CBCFC8;--accent:#2F6E4F}
*{box-sizing:border-box}
body{margin:0;padding:clamp(16px,5vw,56px);background:var(--ground);color:var(--ink);
  font-family:system-ui,-apple-system,"Segoe UI",Cantarell,sans-serif;line-height:1.55;
  display:flex;justify-content:center}
.wrap{max-width:620px;display:flex;flex-direction:column;gap:30px}
h1{font-family:Georgia,"Iowan Old Style",Palatino,serif;font-weight:400;
  font-size:clamp(28px,6vw,40px);margin:0;letter-spacing:-.01em;text-wrap:balance}
.strip{font-family:'RunicSubset',serif;font-size:clamp(20px,5vw,28px);
  color:var(--accent);letter-spacing:.13em;margin:0;word-break:break-all}
p{margin:0;max-width:60ch}
.muted{color:var(--muted)}
.cards{display:grid;gap:14px}
a.card{display:flex;flex-direction:column;gap:4px;padding:20px 22px;
  border:1px solid var(--rule);border-radius:10px;background:var(--panel);
  text-decoration:none;color:inherit}
a.card:hover{border-color:var(--accent)}
a.card:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
a.card b{font-size:17px}
a.card span{color:var(--muted);font-size:14px}
footer{border-top:1px solid var(--rule);padding-top:16px;color:var(--muted);font-size:14px}
footer a{color:var(--accent)}
</style></head><body><div class="wrap">
<header>
  <h1>Norsk med middelalderruner</h1>
  <p class="strip">__STRIP__</p>
  <p class="muted">Et tastaturoppsett, en jukselapp og et spill. Hver norsk
  bokstav ligger på tasten du allerede bruker — æ, ø og å inkludert.</p>
</header>
<div class="cards">
  <a class="card" href="game.html"><b>Runespill</b>
    <span>Ordet står i runer — skriv det på norsk. Fungerer på mobil.</span></a>
  <a class="card" href="runic-cheatsheet.pdf"><b>Jukselapp (PDF)</b>
    <span>Én A4-side. Bygget som et bilde av tastaturet.</span></a>
  <a class="card" href="runic-cheatsheet.html"><b>Jukselapp (nettside)</b>
    <span>Samme side i nettleseren.</span></a>
</div>
<footer>Middelalderruner, ca. 1100–1400. Strengt 1:1 med det norske
alfabetet. <a href="__REPO__">Kildekode og tastaturoppsett på GitHub</a>.</footer>
</div></body></html>
"""

REPO_URL = "https://github.com/jjnuthuagen/norwegian-runic-keyboard"


def build_index():
    strip = "".join(runes.TABLE[c] for c in "abcdefghijklmnopqrstuvwxyzæøå")
    html = (INDEX
            .replace("__FONT__", webfont.css())
            .replace("__STRIP__", strip)
            .replace("__REPO__", REPO_URL))
    OUT.mkdir(parents=True, exist_ok=True)
    page = OUT / "index.html"
    page.write_text(html, encoding="utf-8")
    print(f"  {page.relative_to(OUT.parent.parent)}  ({len(html)} bytes)")


def build():
    build_index()
    html = (PAGE
            .replace("__FONT__", webfont.css())
            .replace("__TABLE__", json.dumps(runes.TABLE, ensure_ascii=False))
            .replace("__WORDS__", json.dumps(WORDS, ensure_ascii=False)))
    OUT.mkdir(parents=True, exist_ok=True)
    page = OUT / "game.html"
    page.write_text(html, encoding="utf-8")
    print(f"  {page.relative_to(OUT.parent.parent)}  ({len(html)} bytes)")


if __name__ == "__main__":
    build()
